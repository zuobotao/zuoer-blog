import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'deploy'))
from monitor import private_address, memory_metrics, probe, process_ticks, process_cpu


class MonitorTests(unittest.TestCase):
    def test_service_cpu_handles_pid_restarts_and_core_normalization(self):
        self.assertEqual(process_cpu({1:10}, {1:110, 2:500}, 1, 100, 4), 25)
        self.assertEqual(process_cpu({1:100}, {1:20}, 1, 100, 4), 0)
        self.assertEqual(process_ticks('1 (a b) S ' + '0 '*10 + '12 8 ' + '0 '*5), 20)
    def test_explicit_source_ranges(self):
        for address in ('127.0.0.1', '::1', '192.168.1.1', '10.1.2.3', '172.16.0.1', 'fd00::1', '::ffff:192.168.1.1'):
            self.assertTrue(private_address(address), address)
        for address in ('8.8.8.8', '100.64.1.1', '169.254.1.1', '198.51.100.1', '192.0.0.1', 'not-an-ip', '2001:db8::1'):
            self.assertFalse(private_address(address), address)

    def test_memory_and_timeout_isolation(self):
        self.assertEqual(memory_metrics('MemTotal: 1000 kB\nMemAvailable: 400 kB\n')['percent'], 60)
        with patch('monitor.urlopen', side_effect=TimeoutError):
            self.assertEqual(probe(('blog','http://127.0.0.1:8080/')), ('blog', {'online':False,'error':'unavailable'}))


if __name__ == '__main__':
    unittest.main()
