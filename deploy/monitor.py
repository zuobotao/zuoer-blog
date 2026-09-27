"""Read-only LAN dashboard. No cloud routes, dependencies or full IP storage."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
from urllib.parse import urlsplit
from urllib.request import urlopen
from analytics import Analytics

PRIVATE = [ipaddress.ip_network(x) for x in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7')]


def private_address(value):
    try:
        address = ipaddress.ip_address(value)
        if address.version == 6 and address.ipv4_mapped:
            address = address.ipv4_mapped
        return address.is_loopback or any(address in network for network in PRIVATE if address.version == network.version)
    except ValueError:
        return False


def memory_metrics(text):
    data = {line.split(':')[0]: int(line.split()[1])*1024 for line in text.splitlines() if ':' in line and len(line.split()) >= 2}
    total = data['MemTotal']
    available = data.get('MemAvailable')
    if available is None:
        available = sum(data.get(key, 0) for key in ('MemFree', 'Buffers', 'Cached'))
    return {'total': total, 'used': max(0, total-available), 'percent': round((total-available)/total*100, 1)}


def process_ticks(text):
    # /proc/<pid>/stat command names can contain whitespace and parentheses.
    fields = text.rsplit(')', 1)[1].split()
    return int(fields[11]) + int(fields[12])


def process_cpu(previous, current, elapsed, ticks_per_second, cores):
    delta = sum(max(0, ticks-previous[pid]) for pid, ticks in current.items() if pid in previous)
    return round(min(100, 100*delta/(elapsed*ticks_per_second*cores)), 1) if elapsed > 0 else None


def probe(item):
    name, url = item
    started = time.monotonic()
    try:
        with urlopen(url, timeout=2) as response:
            result = {'online': response.status == 200, 'ms': round((time.monotonic()-started)*1000)}
            if name == 'rooms':
                data = json.load(response)
                statuses = ('waiting', 'starting', 'playing', 'paused', 'finished', 'closed')
                if set(data) != {'rooms', 'connections'} or set(data['rooms']) != set(statuses):
                    raise ValueError('unexpected room schema')
                if not all(type(value) is int and value >= 0 for value in [data['connections'], *data['rooms'].values()]):
                    raise ValueError('unexpected room counts')
                result['data'] = data
            return name, result
    except Exception:
        return name, {'online': False, 'error': 'unavailable'}


class Sampler:
    def __init__(self, blog_root):
        self.blog_root = Path(blog_root)
        self.analytics = Analytics(self.blog_root / 'data')
        self.previous_cpu = None
        self.previous_processes = None
        self.lock = threading.Lock()
        self.cached = None
        self.sampled_at = 0

    def snapshot(self):
        with self.lock:
            if self.cached and time.monotonic()-self.sampled_at < 4:
                return self.cached
            system = {'cpu': None, 'memory': None, 'disk': None, 'uptime': None, 'temperature': None}
            system['cpuScope'] = 'system'
            try:
                # Exclude guest fields already included in user/nice.
                values = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:9]))
                total, idle = sum(values), values[3] + values[4]
                if self.previous_cpu and total > self.previous_cpu[0]:
                    system['cpu'] = round(100 * (1-(idle-self.previous_cpu[1])/(total-self.previous_cpu[0])), 1)
                self.previous_cpu = (total, idle)
            except (OSError, ValueError, IndexError):
                pass
            if system['cpu'] is None:
                ticks = {}
                for process in Path('/proc').glob('[0-9]*'):
                    try:
                        args = (process/'cmdline').read_bytes().decode().split('\0')
                        if (str(self.blog_root/'serve.py') in args or str(self.blog_root/'monitor.py') in args or
                                ('server/index.ts' in args and any('/ledger101/' in arg for arg in args)) or
                                args[0].endswith('/cloudflared')):
                            ticks[int(process.name)] = process_ticks((process/'stat').read_text())
                    except (OSError, UnicodeError, ValueError, IndexError):
                        pass
                now = time.monotonic()
                if ticks and self.previous_processes:
                    system['cpu'] = process_cpu(self.previous_processes[1], ticks, now-self.previous_processes[0], os.sysconf('SC_CLK_TCK'), os.cpu_count() or 1)
                if ticks:
                    self.previous_processes = (now, ticks)
                    system['cpuScope'] = 'services'
            try:
                system['memory'] = memory_metrics(Path('/proc/meminfo').read_text())
            except (OSError, ValueError, KeyError):
                pass
            try:
                total, used, free = shutil.disk_usage(self.blog_root)
                system['disk'] = {'total': total, 'used': used, 'percent': round(used/total*100, 1)}
            except OSError:
                pass
            try:
                system['uptime'] = float(Path('/proc/uptime').read_text().split()[0])
            except (OSError, ValueError, IndexError):
                try:
                    system['uptime'] = time.clock_gettime(time.CLOCK_BOOTTIME)
                except (AttributeError, OSError):
                    pass
            # Sensor type varies per phone: publish no mislabeled temperature.
            for zone in Path('/sys/class/thermal').glob('thermal_zone*'):
                try:
                    if any(x in (zone/'type').read_text().lower() for x in ('cpu', 'soc')):
                        temp = float((zone/'temp').read_text())/1000
                        if 0 < temp < 150:
                            system['temperature'] = round(temp, 1)
                            break
                except (OSError, ValueError):
                    pass
            urls = [('blog', 'http://127.0.0.1:8080/'), ('game', 'http://127.0.0.1:8081/'), ('roomService', 'http://127.0.0.1:8787/health'), ('rooms', 'http://127.0.0.1:8788/metrics')]
            with ThreadPoolExecutor(max_workers=4) as pool:
                services = dict(pool.map(probe, urls))
            try:
                services['tunnel'] = {'online': subprocess.run(['pgrep', '-x', 'cloudflared'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2).returncode == 0}
            except (OSError, subprocess.TimeoutExpired):
                services['tunnel'] = {'online': None, 'error': 'unavailable'}
            try:
                analytics = self.analytics.summary()
            except Exception:
                analytics = None
            self.cached = {'sampledAt': int(time.time()), 'system': system, 'services': services, 'analytics': analytics}
            self.sampled_at = time.monotonic()
            return self.cached


class MonitorHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, sampler, **kwargs):
        self.sampler = sampler
        super().__init__(*args, **kwargs)

    def log_message(self, *args):
        pass

    def do_GET(self):
        origin = self.headers.get('Origin')
        try:
            host = urlsplit('http://' + self.headers.get('Host', '')).hostname
            origin_host = urlsplit(origin or '').netloc
        except ValueError:
            return self.send_error(403)
        allowed = (private_address(self.client_address[0]) and (host == 'localhost' or private_address(host or ''))
                   and not any(self.headers.get(x) for x in ('CF-Connecting-IP', 'X-Forwarded-For', 'Forwarded'))
                   and (not origin or origin_host == self.headers.get('Host')))
        if not allowed:
            return self.send_error(403)
        if self.path == '/api/metrics':
            content = json.dumps(self.sampler.snapshot()).encode()
            mime = 'application/json; charset=utf-8'
        elif self.path == '/':
            content = Path(__file__).with_name('monitor.html').read_bytes()
            mime = 'text/html; charset=utf-8'
        else:
            return self.send_error(404)
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--blog-root', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('0.0.0.0', args.port), partial(MonitorHandler, sampler=Sampler(args.blog_root)))
    print('LAN monitor listening; private source and Host checks enabled', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
