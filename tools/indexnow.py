#!/usr/bin/env python3
"""Submit the sitemap's URLs to IndexNow.

Bing, Yandex, Seznam and Naver all read IndexNow, and unlike Search Console it
needs no account -- just a key hosted at the site root. That matters here
because Bing had not indexed the site at all, and Bing is what feeds
DuckDuckGo, Yahoo and part of ChatGPT's search.

The key lives in business.json under seo.indexnow_key, and the matching file is
web/<key>.txt. IndexNow fetches that file to prove we control the domain, so
the key must be deployed BEFORE submitting -- this script checks that first and
refuses rather than burning a submission.

    python3 tools/indexnow.py            # submit every sitemap URL
    python3 tools/indexnow.py --check    # verify the key is live, submit nothing
"""
import json, os, sys, urllib.request, urllib.error, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "business.json"), encoding="utf-8"))
HOST = CFG["domain"]
BASE = CFG["url"].rstrip("/")
KEY = (CFG.get("seo") or {}).get("indexnow_key")
ENDPOINT = "https://api.indexnow.org/IndexNow"
UA = "Mozilla/5.0 (compatible; TampaMaidsIndexNow/1.0)"


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def key_is_live():
    """IndexNow rejects the whole batch if it cannot fetch the key file."""
    url = "%s/%s.txt" % (BASE, KEY)
    try:
        body = _get(url).strip()
    except Exception as e:
        return False, "%s -> %s" % (url, e)
    if body != KEY:
        return False, "%s served %r, expected the key itself" % (url, body[:40])
    return True, url


def sitemap_urls():
    xml = _get("%s/sitemap.xml" % BASE)
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)


def submit(urls):
    payload = json.dumps({"host": HOST, "key": KEY,
                          "keyLocation": "%s/%s.txt" % (BASE, KEY),
                          "urlList": urls}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=payload, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8",
                                          "User-Agent": UA})
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, (r.read() or b"").decode("utf-8", "replace")[:200]
    except urllib.error.HTTPError as e:
        return e.code, (e.read() or b"").decode("utf-8", "replace")[:200]


def main():
    if not KEY:
        sys.exit("No seo.indexnow_key in business.json.")
    ok, detail = key_is_live()
    print("key file: %s" % detail)
    if not ok:
        sys.exit("Key file is not live yet -- deploy first, then run this again.")
    if "--check" in sys.argv:
        return
    urls = sitemap_urls()
    if not urls:
        sys.exit("sitemap.xml returned no URLs.")
    status, body = submit(urls)
    print("submitted %d urls -> HTTP %s %s" % (len(urls), status, body))
    # 200 accepted, 202 accepted but key still being validated.
    if status not in (200, 202):
        sys.exit(1)


if __name__ == "__main__":
    main()
