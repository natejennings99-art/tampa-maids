"""The health check endpoint.

Render pings healthCheckPath constantly and takes the service out of rotation
when it stops answering, so a break here takes the whole site down rather than
degrading one page. That makes it worth a real request against a live socket
instead of a unit test on a helper.
"""
import os, sys, tempfile, threading, unittest, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# db.py reads DATA_DIR at import time, so point it at a throwaway directory
# before app.py pulls it in — otherwise the test would open the real database.
_TMP = tempfile.mkdtemp(prefix="tm-health-")
os.environ["DATA_DIR"] = _TMP

sys.path.insert(0, os.path.join(ROOT, "server"))
import app  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402


class HealthCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.port = cls.srv.server_address[1]
        cls.thread = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def get(self, path):
        url = "http://127.0.0.1:%d%s" % (self.port, path)
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                return r.status, r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def test_healthz_answers_ok(self):
        status, body = self.get("/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(body.strip(), "ok")

    def test_healthz_needs_no_database(self):
        """The whole point of a separate path: it must not depend on the disk
        or the config, so it still answers when those are broken."""
        self.assertFalse(
            os.path.exists(os.path.join(_TMP, "bookings.db")),
            "GET /healthz touched the database; it should answer before any I/O",
        )

    def test_healthz_is_not_logged(self):
        self.assertIn("/healthz", app.Handler.QUIET_PATHS)

    def test_real_requests_are_still_logged(self):
        """Suppressing the health check must not suppress anything else — the
        access log is how a booking gets noticed while mail is unconfigured."""
        self.assertNotIn("/api/config", app.Handler.QUIET_PATHS)
        self.assertNotIn("/", app.Handler.QUIET_PATHS)


if __name__ == "__main__":
    unittest.main()
