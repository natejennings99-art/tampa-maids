"""Internal linking tests.

A page nothing links to does not rank, and a page only the hub links to barely
ranks. The neighbourhood pages are the long-tail of the site, so these guard
against link equity quietly pooling on a handful of them.

Run:  python3 -m unittest discover -s tests
"""
import collections, os, re, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")


def _pages():
    out = {}
    for root, _, files in os.walk(WEB):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(root, f)
            url = "/" + os.path.relpath(path, WEB).replace(os.sep, "/")[:-len(".html")]
            with open(path, encoding="utf-8") as fh:
                out[url] = fh.read()
    return out


def _sitemap_urls():
    with open(os.path.join(WEB, "sitemap.xml"), encoding="utf-8") as fh:
        xml = fh.read()
    return [u.replace("https://tampamaidscleaning.com", "") or "/"
            for u in re.findall(r"<loc>([^<]+)</loc>", xml)]


@unittest.skipUnless(os.path.isdir(WEB), "site not built")
class InternalLinks(unittest.TestCase):
    def setUp(self):
        self.pages = _pages()
        self.inbound = collections.Counter()
        for url, html in self.pages.items():
            for href in set(re.findall(r'href="(/[^"#?]*)', html)):
                h = href.rstrip("/") or "/"
                if h != url.rstrip("/"):
                    self.inbound[h] += 1

    def test_no_page_in_the_sitemap_is_an_orphan(self):
        orphans = [u for u in _sitemap_urls()
                   if self.inbound[u.rstrip("/") or "/"] == 0]
        self.assertEqual(orphans, [], "nothing links to these: %s" % orphans)

    def test_neighbourhood_links_are_shared_evenly_within_a_market(self):
        # Regression: the "nearby areas" block used a fixed [:5] slice, so the
        # earliest areas in each market took every internal link and the rest
        # were left with only the hub -- a 1-versus-9 spread across Tampa.
        markets = collections.defaultdict(list)
        for url in self.pages:
            parts = url.strip("/").split("/")
            if len(parts) == 3 and parts[0] == "cleaning":
                markets[parts[1]].append(url)
        self.assertTrue(markets, "no neighbourhood pages found")
        for market, urls in markets.items():
            counts = [self.inbound[u.rstrip("/")] for u in urls]
            self.assertGreaterEqual(min(counts), 2,
                                    "%s has a starved page: %s" % (market, dict(zip(urls, counts))))
            self.assertLessEqual(max(counts) - min(counts), 2,
                                 "%s link spread too wide: %s" % (market, dict(zip(urls, counts))))


if __name__ == "__main__":
    unittest.main()
