"""Ad tags render only when their env vars are set, and never on staff pages."""
import os, sys, tempfile, threading, unittest, urllib.request
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="tm-tags-"))
sys.path.insert(0, os.path.join(ROOT, "server"))
import app, db, tags  # noqa: E402

VARS = ("META_PIXEL_ID", "GOOGLE_TAG_ID", "GOOGLE_ADS_ID",
        "GOOGLE_ADS_LEAD_LABEL", "GOOGLE_ADS_PURCHASE_LABEL")


class TagsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db.init()
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self._saved = {k: os.environ.pop(k, None) for k in VARS}

    def tearDown(self):
        for k, v in self._saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v

    def page(self, path):
        with urllib.request.urlopen(self.base + path, timeout=5) as r:
            return r.read().decode(), r.headers.get("ETag")

    def test_nothing_loads_when_unset(self):
        html, _ = self.page("/")
        for needle in ("TM_TAGS", "fbevents.js", "googletagmanager.com"):
            self.assertNotIn(needle, html)

    def test_meta_and_google_render_when_set(self):
        _, plain_etag = self.page("/")
        os.environ["META_PIXEL_ID"] = "123456789012345"
        os.environ["GOOGLE_TAG_ID"] = "G-ABC1234567"
        os.environ["GOOGLE_ADS_ID"] = "AW-987654321"
        html, etag = self.page("/")
        head = html[:html.lower().index("</head>")]
        self.assertIn("fbq('init','123456789012345')", head)
        self.assertIn('<script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC1234567">', head)
        self.assertIn("gtag('config','AW-987654321')", head)
        self.assertNotEqual(etag, plain_etag, "a cached untagged page would hide the tags")
        for path in ("/book", "/pricing", "/contact"):
            self.assertIn("TM_TAGS", self.page(path)[0], path)

    def test_only_google_when_only_google_is_set(self):
        os.environ["GOOGLE_TAG_ID"] = "G-ABC1234567"
        html, _ = self.page("/book")
        self.assertIn("googletagmanager.com", html)
        self.assertNotIn("fbevents.js", html)

    def test_staff_pages_are_never_tagged(self):
        os.environ["META_PIXEL_ID"] = "123456789012345"
        for path in ("/owner", "/admin/"):
            self.assertNotIn("TM_TAGS", self.page(path)[0], path)

    def test_malformed_ids_are_ignored(self):
        os.environ["META_PIXEL_ID"] = "123</script><script>alert(1)"
        os.environ["GOOGLE_TAG_ID"] = "G-abc'+x"
        self.assertEqual(tags.snippet(), "")
        self.assertNotIn("alert(1)", self.page("/")[0])

    def test_events_are_wired_where_leads_and_payments_happen(self):
        js = lambda f: open(os.path.join(ROOT, "web", "js", f), encoding="utf-8").read()
        self.assertIn("function tmTrack", js("api.js"))
        self.assertIn("generate_lead", js("api.js"))
        self.assertIn("'Purchase'", js("api.js"))
        self.assertIn("tmTrack('lead'", js("booking.js"))
        self.assertIn("tmTrack('lead'", js("contact.js"))
        self.assertIn("tmTrack('purchase'", js("track.js"))


if __name__ == "__main__":
    unittest.main()
