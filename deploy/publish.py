"""Run on the existing Termux host after uploading a dist/deploy bundle.

Archives and previous releases are retained. Secrets and data stay on device.
Room restart must be explicitly authorized before running this release script.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tarfile
import time
from urllib.request import Request, urlopen


def wait_http(url, attempts=40):
    for attempt in range(attempts):
        try:
            with urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return response.read()
        except Exception:
            pass
        time.sleep(.25)
    raise RuntimeError('Service did not become ready: ' + url)


def swap_link(link, target):
    pending = link.with_name(link.name + '.next')
    if pending.is_symlink():
        pending.unlink()
    assert not pending.exists(), 'Unexpected pending path'
    pending.symlink_to(target)
    pending.replace(link)


def matching_processes(root, argument):
    found = []
    for path in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            args = path.read_bytes().decode().split('\0')
            if argument in args and any(str(root) in arg for arg in args) and args[0].endswith(('python3', 'node')):
                found.append(int(path.parent.name))
        except (OSError, ValueError, UnicodeError):
            pass
    return found


def stop_processes(pids):
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    for attempt in range(40):
        alive = []
        for pid in pids:
            try:
                os.kill(pid, 0)
                alive.append(pid)
            except ProcessLookupError:
                pass
        if not alive:
            return
        time.sleep(.1)
    raise RuntimeError('Processes did not stop cleanly; no forced termination')


def main(archive):
    os.umask(0o077)
    home = Path.home()
    blog, ledger = home/'zuoer-blog', home/'ledger101'
    stamp = time.strftime('analytics-monitor-%Y%m%d-%H%M%S')
    release = blog/'releases'/stamp
    release.mkdir(parents=True)
    with tarfile.open(archive) as bundle:
        bundle.extractall(release, filter='data')
    source = release/'deploy'
    assert (release/'dist/index.html').is_file()
    config = home/'.cloudflared/config.yml'
    if config.exists():
        assert ':8765' not in config.read_text() and ':8788' not in config.read_text(), 'Monitor ports must not be tunneled'
    subprocess.run(['python3', '-m', 'unittest', 'discover', '-s', str(release/'tests'), '-p', 'test_*.py'], check=True, cwd=release)

    # Clone only the server sources and existing configuration into a new release.
    old_blog = (blog/'current').resolve()
    old_ledger = (ledger/'current').resolve()
    new_ledger = ledger/'releases'/stamp
    shutil.copytree(old_ledger, new_ledger, symlinks=True, ignore=shutil.ignore_patterns('node_modules'))
    (new_ledger/'node_modules').symlink_to(old_ledger/'node_modules')
    spec = importlib.util.spec_from_file_location('installer', source/'install-ledger-metrics.py')
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    installer.install(new_ledger, source/'ledger-metrics.ts')
    env = {**os.environ, 'HOST':'127.0.0.1', 'ROOM_PORT':'18877', 'ROOM_METRICS_PORT':'18878', 'TSX_TSCONFIG_PATH':str(new_ledger/'tsconfig.server.json')}
    with (release/'candidate.log').open('w') as log:
        candidate = subprocess.Popen(['node', str(new_ledger/'node_modules/.bin/tsx'), 'server/index.ts'], cwd=new_ledger, env=env, stdout=log, stderr=log, start_new_session=True)
        try:
            wait_http('http://127.0.0.1:18877/health')
            snapshot = json.loads(wait_http('http://127.0.0.1:18878/metrics'))
            assert set(snapshot) == {'rooms', 'connections'} and snapshot['connections'] == 0
            req = Request('http://127.0.0.1:18877/rooms', data=json.dumps({'sessionId':'release-smoke-test', 'nickname':'release-check'}).encode(), headers={'Content-Type':'application/json'})
            with urlopen(req, timeout=3) as response:
                assert response.status == 200
            assert json.loads(wait_http('http://127.0.0.1:18878/metrics'))['rooms']['waiting'] == 1
        finally:
            os.killpg(candidate.pid, signal.SIGTERM)
            candidate.wait(timeout=5)

    backup = release/'previous-runtime'
    backup.mkdir()
    runtime = ['serve.py', 'analytics.py', 'monitor.py', 'monitor.html']
    existed = {}
    for name in runtime:
        existed[name] = (blog/name).exists()
        if existed[name]:
            shutil.copy2(blog/name, backup/name)
    blog_pids = matching_processes(blog, str(blog/'serve.py'))
    room_pids = matching_processes(ledger, 'server/index.ts')
    assert blog_pids and room_pids, 'Cannot identify existing service processes safely'
    boot = home/'.termux/boot'
    monitor_boot = boot/'20-zuoer-monitor'
    had_monitor_boot = monitor_boot.exists()
    if had_monitor_boot:
        shutil.copy2(monitor_boot, backup/'20-zuoer-monitor')
    (release/'rollback.json').write_text(json.dumps({'blog':str(old_blog), 'ledger':str(old_ledger), 'runtime':existed}))
    try:
        for name in runtime:
            shutil.copy2(source/name, blog/name)
        shutil.copy2(source/'termux/20-zuoer-monitor', monitor_boot)
        monitor_boot.chmod(0o700)
        swap_link(blog/'current', release/'dist')
        swap_link(ledger/'current', new_ledger)
        stop_processes(blog_pids + room_pids)
        subprocess.run(['bash', str(boot/'10-zuoer-server')], check=True)
        wait_http('http://127.0.0.1:8080/api/analytics/counts')
        wait_http('http://127.0.0.1:8081/')
        wait_http('http://127.0.0.1:8787/health')
        wait_http('http://127.0.0.1:8788/metrics')
        subprocess.run(['bash', str(monitor_boot)], check=True)
        wait_http('http://127.0.0.1:8765/api/metrics')
        subprocess.run(['bash', str(monitor_boot)], check=True)
    except Exception:
        stop_processes(matching_processes(blog, str(blog/'serve.py')) + matching_processes(ledger, 'server/index.ts'))
        swap_link(blog/'current', old_blog)
        swap_link(ledger/'current', old_ledger)
        for name in runtime:
            if existed[name]:
                shutil.copy2(backup/name, blog/name)
        if had_monitor_boot:
            shutil.copy2(backup/'20-zuoer-monitor', monitor_boot)
        else:
            if monitor_boot.exists():
                monitor_boot.replace(backup/'20-zuoer-monitor-unused')
            stop_processes(matching_processes(blog, str(blog/'monitor.py')))
        subprocess.run(['bash', str(boot/'10-zuoer-server')], check=True)
        raise
    print('Published', stamp, 'with existing boot script preserved and rollback release retained')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    main(args.archive)
