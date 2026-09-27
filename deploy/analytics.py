"""First-party, IP-estimated visit counts. Never persist full IPs or URLs."""

import hashlib
import hmac
import ipaddress
from contextlib import contextmanager
import os
from pathlib import Path
import secrets
import sqlite3
import time
from urllib.parse import urlsplit

RETENTION = 90 * 86400


def client_ip(peer, headers):
    address = ipaddress.ip_address(peer)
    if address.is_loopback:
        try:
            return str(ipaddress.ip_address(headers.get('CF-Connecting-IP', peer)))
        except ValueError:
            pass
    return str(address)


def mask_ip(address):
    address = ipaddress.ip_address(address)
    return str(ipaddress.ip_network(f'{address}/{24 if address.version == 4 else 48}', strict=False))


def canonical_path(path):
    path = urlsplit(path).path
    if path.startswith('/en/'):
        path = path[3:]
    return path if path.endswith('/') else path + '/'


class Analytics:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        key = self.directory / 'visitor.key'
        try:
            with key.open('xb') as file:
                os.chmod(key, 0o600)
                file.write(secrets.token_bytes(32))
        except FileExistsError:
            pass
        self.key = key.read_bytes()
        self.database = self.directory / 'analytics.sqlite3'
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS visits (ts INTEGER, path TEXT, visitor TEXT, network TEXT, source TEXT, device TEXT)')
            db.execute('CREATE INDEX IF NOT EXISTS visit_lookup ON visits(visitor, path, ts)')
            db.execute('CREATE INDEX IF NOT EXISTS visit_time ON visits(ts)')
        os.chmod(self.database, 0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=3)
        try:
            with db:
                yield db
        finally:
            db.close()

    def record(self, path, address, source='', agent='', now=None):
        now = int(time.time() if now is None else now)
        visitor = hmac.new(self.key, address.encode(), hashlib.sha256).hexdigest()
        network = mask_ip(address)
        # Only a host, never full URLs, query parameters, paths or fragments.
        source = urlsplit(source).hostname if source.startswith(('http://', 'https://')) else None
        source = (source or 'direct')[:253]
        device = 'mobile' if any(x in agent.lower() for x in ['mobile', 'android', 'iphone']) else 'desktop'
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM visits WHERE ts < ?', (now - RETENTION,))
            if db.execute('SELECT 1 FROM visits WHERE visitor=? AND path=? AND ts>? LIMIT 1', (visitor, canonical_path(path), now - 1800)).fetchone():
                return False
            db.execute('INSERT INTO visits VALUES (?, ?, ?, ?, ?, ?)', (now, canonical_path(path), visitor, network, source, device))
        return True

    def counts(self, path='/', now=None):
        cutoff = int(time.time() if now is None else now) - RETENTION
        with self.connect() as db:
            db.execute('DELETE FROM visits WHERE ts < ?', (cutoff,))
            pv, uv = db.execute('SELECT COUNT(*), COUNT(DISTINCT visitor) FROM visits WHERE ts>=?', (cutoff,)).fetchone()
            readers = db.execute('SELECT COUNT(DISTINCT visitor) FROM visits WHERE ts>=? AND path=?', (cutoff, canonical_path(path))).fetchone()[0]
        return {'views': pv, 'visitors': uv, 'readers': readers, 'windowDays': 90}

    def summary(self):
        cutoff = int(time.time()) - RETENTION
        with self.connect() as db:
            tables = {}
            for name, column in [('pages', 'path'), ('sources', 'source'), ('networks', 'network'), ('devices', 'device')]:
                rows = db.execute(f'SELECT {column}, COUNT(*), COUNT(DISTINCT visitor) FROM visits WHERE ts>=? GROUP BY {column} ORDER BY COUNT(*) DESC LIMIT 20', (cutoff,)).fetchall()
                tables[name] = [{'label': label, 'views': views, 'visitors': visitors} for label, views, visitors in rows]
            rows = db.execute("SELECT strftime('%Y-%m-%d', ts, 'unixepoch', '+8 hours'), COUNT(*), COUNT(DISTINCT visitor) FROM visits WHERE ts>=? GROUP BY 1 ORDER BY 1", (max(cutoff, int(time.time())-30*86400),)).fetchall()
            tables['daily'] = [{'label': day, 'views': views, 'visitors': visitors} for day, views, visitors in rows]
        return {**self.counts(), **tables}
