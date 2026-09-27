import json
import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'deploy'))
from analytics import Analytics, client_ip, canonical_path, mask_ip


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Analytics(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_deduplication_languages_and_readers(self):
        self.assertTrue(self.store.record('/articles/one/', '203.0.113.12', now=10000))
        self.assertFalse(self.store.record('/en/articles/one/', '203.0.113.12', now=10001))
        self.assertTrue(self.store.record('/articles/one/', '203.0.113.12', now=12000))
        self.assertTrue(self.store.record('/articles/one/', '203.0.113.13', now=12001))
        self.assertEqual(self.store.counts('/en/articles/one/', now=12002), {'views': 3, 'visitors': 2, 'readers': 2, 'windowDays': 90})

    def test_only_loopback_can_supply_cloudflare_client(self):
        self.assertEqual(client_ip('192.168.1.10', {'CF-Connecting-IP':'203.0.113.12'}), '192.168.1.10')
        self.assertEqual(client_ip('127.0.0.1', {'CF-Connecting-IP':'203.0.113.12'}), '203.0.113.12')
        self.assertEqual(client_ip('127.0.0.1', {'CF-Connecting-IP':'invalid'}), '127.0.0.1')

    def test_private_data_never_persisted(self):
        self.store.record('/articles/one/?secret=hidden', '203.0.113.12', 'https://example.org/private?secret=hidden', 'PrivateBrowser Android')
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM visits').fetchone()
        payload = json.dumps(row)
        for private in ('203.0.113.12', 'secret', '/private', 'PrivateBrowser'):
            self.assertNotIn(private, payload)
        self.assertIn('203.0.113.0/24', payload)
        self.assertIn('example.org', payload)
        self.assertEqual(mask_ip('2001:db8:1:abcd::12'), '2001:db8:1::/48')

    def test_retention_and_restart(self):
        self.store.record('/', '203.0.113.12', now=1)
        self.assertEqual(self.store.counts(now=91*86400)['views'], 0)
        self.store.record('/', '203.0.113.13', now=91*86400)
        self.assertEqual(Analytics(self.temp.name).counts(now=91*86400)['visitors'], 1)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM visits').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
