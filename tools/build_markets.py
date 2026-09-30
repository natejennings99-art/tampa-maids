#!/usr/bin/env python3
"""Generates one local-SEO landing page per market, plus sitemap.xml and robots.txt.

The business plan names local SEO service-area pages and Google Local Services
Ads as the highest-ROI acquisition channel. Each page targets one market with
its own H1, copy, community list, schema and canonical URL, so they don't read
as duplicate content.

    python3 tools/build_markets.py
"""
import os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import page, CFG, NAME, ORIGIN, WEB
from inner_v2 import market_page as market_body

MARKETS = CFG["markets"]


def slug(n):
    out = "".join(c.lower() if c.isalnum() else "-" for c in n)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


# A distinct angle per market so the pages aren't near-duplicates.
ANGLES = {
    "tampa": ("Our crews start their day here, which means Tampa addresses get the "
              "widest choice of arrival windows and the shortest notice we can offer. "
              "South Tampa and Hyde Park bungalows, Westchase and Carrollwood family "
              "homes, Brandon and Riverview new-builds — we clean all of it."),
    "st-petersburg": ("Downtown St. Pete condos, Snell Isle homes, and a heavy "
                      "vacation-rental load out on the beaches. If you host on Airbnb or "
                      "VRBO in St. Pete Beach or Treasure Island, our turnover crews run a "
                      "28-point checklist with photo verification and a same-day SLA."),
    "clearwater": ("North Pinellas homes plus one of the busiest beach-rental corridors in "
                   "Florida. We handle recurring house cleaning in Largo, Seminole, Dunedin "
                   "and Safety Harbor, and same-day turnovers on Clearwater Beach."),
    "sarasota": ("Our newest market, south across the Skyway. Sarasota, Siesta Key, Longboat "
                 "Key and Lakewood Ranch — recurring home cleaning, seasonal opens and "
                 "closes for snowbird properties, and rental turnovers on the keys. A small "
                 "drive-time surcharge applies down here; it's shown in your quote before "
                 "you book, never added afterwards."),
}


def market_page(m):
    s = slug(m["name"])
    areas = m["areas"]
    angle = ANGLES.get(s, m["blurb"])
    surcharged = [a for a in areas
                  if a in (CFG.get("surcharge_zones", {}).get("cities") or {})]

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "HouseCleaningService",
        "name": "%s — %s" % (NAME, m["name"]),
        "url": "%s/cleaning/%s" % (ORIGIN, s),
        "image": ORIGIN + "/icons/icon-512.png",
        "description": "House and commercial cleaning in %s, Florida." % m["name"],
        "telephone": CFG["phone"],
        "email": CFG["email"],
        "priceRange": "$$",
        "address": {"@type": "PostalAddress", "addressLocality": CFG["city"],
                    "addressRegion": CFG["state"], "addressCountry": "US"},
        "areaServed": [{"@type": "City", "name": a} for a in areas],
    }, indent=2)

    body = market_body(CFG, m, angle, surcharged)

    page("cleaning/%s.html" % s,
         "Cleaning Services in %s, FL | %s" % (m["name"], NAME),
         "House cleaning, deep cleans and move-out cleaning in %s. Bonded, insured, "
         "background-checked team. Flat upfront pricing, book online."
         % m["name"],
         body,
         head='<script type="application/ld+json">%s</script>' % schema,
         scripts='<script src="/js/home.js"></script>', photo=s)


for m in MARKETS:
    market_page(m)

# ---------------- sitemap + robots ----------------
urls = ["/", "/services", "/pricing", "/about", "/faq", "/contact", "/book", "/track"]
urls += ["/cleaning/%s" % slug(m["name"]) for m in MARKETS]
sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "".join('  <url><loc>%s%s</loc><priority>%s</priority></url>\n'
                     % (ORIGIN, u if u != "/" else "/", "1.0" if u == "/" else "0.8")
                     for u in urls)
           + '</urlset>\n')
open(os.path.join(WEB, "sitemap.xml"), "w", encoding="utf-8").write(sitemap)

robots = ("User-agent: *\n"
          "Allow: /\n"
          "Disallow: /admin\n"
          "Disallow: /api/\n\n"
          "Sitemap: %s/sitemap.xml\n" % ORIGIN)
open(os.path.join(WEB, "robots.txt"), "w", encoding="utf-8").write(robots)

print("  wrote web/sitemap.xml (%d urls) and web/robots.txt" % len(urls))
print("\n  build_markets.py: %d market pages done" % len(MARKETS))
