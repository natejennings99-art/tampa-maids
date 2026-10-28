"""Server-side Purchase events (Meta CAPI, GA4 Measurement Protocol)."""
import json, os, sys, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="tm-conv-"))
sys.path.insert(0, os.path.join(ROOT, "server"))
import conversions  # noqa: E402

VARS = ("META_PIXEL_ID", "META_CAPI_TOKEN", "GOOGLE_TAG_ID", "GA_API_SECRET")


class Sink(BaseHTTPRequestHandler):
    hits = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        Sink.hits.append((self.path, json.loads(self.rfile.read(n))))
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()


class ConversionsTest(unittest.TestCase):

    def setUp(self):
        self._saved = {k: os.environ.pop(k, None) for k in VARS}
        Sink.hits = []

    def tearDown(self):
        for k, v in self._saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v

    def test_off_without_keys(self):
        os.environ["META_PIXEL_ID"] = "123456789012345"     # pixel alone is not enough
        self.assertIsNone(conversions.purchase("TM-A", 15000, "a@b.co", "8135550100", {}))

    def test_capture_keeps_only_well_formed_ids(self):
        ids = conversions.capture({"_ga": "GA1.1.123456.1700000000",
                                   "_fbp": "fb.1.1700000000.987654",
                                   "_fbc": "<script>"}, "Mozilla/5.0")
        self.assertEqual(ids, {"ga_cid": "123456.1700000000",
                               "fbp": "fb.1.1700000000.987654", "ua": "Mozilla/5.0"})

    def test_meta_payload_hashes_pii_and_matches_the_browser_event_id(self):
        p = conversions.meta_payload("TM-ABC", 18500, " Jo@Example.com ", "(813) 555-0100",
                                     {"fbp": "fb.1.1.2"}, now=1)["data"][0]
        self.assertEqual(p["event_id"], "purchase-TM-ABC")   # browser: 'purchase-' + ref
        self.assertEqual(p["custom_data"]["value"], 185.0)
        self.assertEqual(len(p["user_data"]["em"][0]), 64)
        self.assertNotIn("Jo@Example.com", json.dumps(p))
        self.assertEqual(p["user_data"]["ph"][0],
                         conversions._sha("18135550100"))

    def test_ga_payload_uses_the_visitor_client_id(self):
        p = conversions.ga_payload("TM-ABC", 18500, {"ga_cid": "1.2"})
        self.assertEqual((p["client_id"], p["events"][0]["params"]["transaction_id"]),
                         ("1.2", "TM-ABC"))

    def test_sends_to_both_when_configured(self):
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Sink)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = "http://127.0.0.1:%d" % srv.server_address[1]
        old = conversions.META_API, conversions.GA_API
        conversions.META_API = conversions.GA_API = base
        os.environ.update(META_PIXEL_ID="123456789012345", META_CAPI_TOKEN="tok",
                          GOOGLE_TAG_ID="G-ABC1234567", GA_API_SECRET="sec")
        try:
            conversions.purchase("TM-XYZ", 15000, "a@b.co", "8135550100", {}, wait=True)
        finally:
            conversions.META_API, conversions.GA_API = old
            srv.shutdown(); srv.server_close()
        paths = sorted(h[0].split("?")[0] for h in Sink.hits)
        self.assertEqual(paths, ["/123456789012345/events", "/mp/collect"])


if __name__ == "__main__":
    unittest.main()
