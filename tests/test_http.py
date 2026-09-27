from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'deploy'))
from analytics import Analytics
from serve import BlogHandler
from monitor import MonitorHandler


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'index.html').write_text('Home')
        BlogHandler.analytics = Analytics(self.root/'data')
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(BlogHandler, directory=str(self.root)))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def post(self, data, **headers):
        req = Request(self.url+'/api/analytics/view', data=json.dumps(data).encode(), headers={'Origin':self.url, 'User-Agent':'Mozilla/5.0', 'Content-Type':'application/json', **headers})
        with urlopen(req) as response:
            return json.load(response)

    def test_tracking_counts_dnt_and_path_bounds(self):
        self.assertTrue(self.post({'path':'/'})['recorded'])
        self.assertFalse(self.post({'path':'/'})['recorded'])
        self.assertFalse(self.post({'path':'/'}, DNT='1')['recorded'])
        with urlopen(self.url+'/api/analytics/counts?path=/en/') as response:
            data = json.load(response)
        self.assertEqual(data['views'], 1)
        self.assertEqual(data['readers'], 1)
        for path in ['/../../private', '/made-up/']:
            with self.assertRaises(HTTPError) as error:
                self.post({'path':path})
            self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error:
            self.post({'path':'/'}, Origin='https://elsewhere.example')
        self.assertEqual(error.exception.code, 403)

    def test_lan_panel_rejects_proxy_and_rebinding_hosts(self):
        class FakeSampler:
            def snapshot(self):
                return {'ok':True}
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(MonitorHandler, sampler=FakeSampler()))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}/api/metrics'
        try:
            with urlopen(url) as response:
                self.assertTrue(json.load(response)['ok'])
            for headers in [{'Host':'attacker.example'}, {'CF-Connecting-IP':'192.168.1.1'}, {'X-Forwarded-For':'10.0.0.1'}, {'Origin':'https://attacker.example'}]:
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(url, headers=headers))
                self.assertEqual(error.exception.code, 403)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
