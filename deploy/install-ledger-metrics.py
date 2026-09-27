"""Install a narrowly scoped, idempotent source adapter in a release copy."""
import argparse
from pathlib import Path
import shutil


def install(root, module):
    root = Path(root)
    files = {name: (root/'server'/name).read_text() for name in ('index.ts', 'RoomServer.ts', 'room/RoomManager.ts')}
    index = files['index.ts']
    if "import { startRoomMetrics } from './monitor'" not in index:
        marker = 'const roomServer = new RoomServer(http)'
        assert index.count(marker) == 1, 'Unsupported Ledger entry point'
        index = "import { startRoomMetrics } from './monitor'\n" + index.replace(marker, marker + '\nstartRoomMetrics(() => roomServer.getMetrics())')
    server = files['RoomServer.ts']
    if 'getMetrics()' not in server:
        marker = '  // ==================== HTTP Bootstrap ===================='
        assert server.count(marker) == 1, 'Unsupported RoomServer layout'
        method = '''  getMetrics() {
    let connections = 0
    for (const group of this.roomConns.values()) {
      for (const conn of group) if (conn.readyState === 1) connections++
    }
    return { rooms: this.roomManager.getRoomStatusCounts(), connections }
  }

'''
        server = server.replace(marker, method + marker)
    manager = files['room/RoomManager.ts']
    if 'getRoomStatusCounts()' not in manager:
        marker = '  // ==================== Create ===================='
        assert manager.count(marker) == 1, 'Unsupported RoomManager layout'
        method = '''  getRoomStatusCounts(): Record<string, number> {
    return aggregateRoomMetrics(this.repo.all(), []).rooms
  }

'''
        manager = manager.replace(marker, method + marker)
        manager = "import { aggregateRoomMetrics } from '../monitor'\n" + manager
    # Validate every source anchor before any write; caller uses an isolated copy.
    for name, content in [('index.ts', index), ('RoomServer.ts', server), ('room/RoomManager.ts', manager)]:
        (root/'server'/name).write_text(content)
    shutil.copyfile(module, root/'server/monitor.ts')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    install(args.root, Path(__file__).with_name('ledger-metrics.ts'))
