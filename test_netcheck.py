import socket
import threading
import unittest

import netcheck


class NetcheckTests(unittest.TestCase):
    def setUp(self):
        # Start a tiny local TCP server so the tests do not depend on the internet.
        self.server = socket.socket()
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(5)
        self.port = self.server.getsockname()[1]
        self.thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.running = True
        self.thread.start()

    def _accept_loop(self):
        self.server.settimeout(0.2)
        while self.running:
            try:
                conn, _ = self.server.accept()
                conn.close()
            except OSError:
                pass

    def tearDown(self):
        self.running = False
        self.thread.join()
        self.server.close()

    def test_open_port_is_up(self):
        target = {"name": "local", "host": "127.0.0.1", "port": self.port}
        result = netcheck.check_target(target, attempts=3, timeout=1, slow_ms=500)
        self.assertEqual(result["status"], "UP")
        self.assertEqual(result["loss_pct"], 0)

    def test_closed_port_is_down(self):
        target = {"name": "closed", "host": "127.0.0.1", "port": 1}
        result = netcheck.check_target(target, attempts=2, timeout=0.5, slow_ms=500)
        self.assertEqual(result["status"], "DOWN")
        self.assertEqual(result["loss_pct"], 100)

    def test_unknown_host_is_dns_fail(self):
        target = {"name": "bad", "host": "this-host-does-not-exist.invalid", "port": 80}
        result = netcheck.check_target(target, attempts=1, timeout=0.5, slow_ms=500)
        self.assertEqual(result["status"], "DNS_FAIL")


if __name__ == "__main__":
    unittest.main()
