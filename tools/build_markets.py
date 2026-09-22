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
    others = [x for x in MARKETS if x["name"] != m["name"]]
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

    body = '''
<section style="background:linear-gradient(170deg,var(--teal-50),#fff);padding-bottom:40px">
  <div class="wrap narrow center">
    <p class="eyebrow">%(name)s, Florida</p>
    <h1>House &amp; office cleaning in %(name)s</h1>
    <p class="lede" style="margin-inline:auto">%(angle)s</p>
    <div class="btn-row" style="justify-content:center;margin-top:24px">
      <a class="btn btn-primary btn-lg" href="/book">See your %(name)s price</a>
      <a class="btn btn-ghost btn-lg" data-biz-href="phone" href="#">Call us</a>
    </div>
    <p class="muted" style="margin-top:18px;font-size:.9rem">%(home)s</p>
  </div>
</section>

<section style="padding-top:44px">
  <div class="wrap">
    <div class="center" style="margin-bottom:34px">
      <p class="eyebrow">Coverage</p>
      <h2>Where we clean around %(name)s</h2>
    </div>
    <div class="chips" style="justify-content:center;max-width:760px;margin:0 auto">%(chips)s</div>
    %(sur)s
  </div>
</section>

<section class="tint">
  <div class="wrap">
    <div class="center" style="margin-bottom:40px">
      <p class="eyebrow">Pricing in %(name)s</p>
      <h2>Flat rates, published openly</h2>
      <p class="lede">The same published price list everywhere we work. No hourly meter,
      no estimate that changes at the door.</p>
    </div>
    <div class="table-scroll" style="max-width:900px;margin:0 auto">
      <table class="ptable" id="tierTable"></table></div>
    <p class="hint center" id="firstNote" style="margin-top:14px"></p>
    <div class="center" style="margin-top:26px">
      <a class="btn btn-primary btn-lg" href="/book">Get my exact price</a></div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="center" style="margin-bottom:40px">
      <p class="eyebrow">Services</p>
      <h2>What we do in %(name)s</h2>
    </div>
    <div class="grid grid-3" id="svcGrid"></div>
  </div>
</section>

<section class="tint-teal">
  <div class="wrap">
    <div class="center" style="margin-bottom:36px">
      <p class="eyebrow">Why us</p>
      <h2>The difference is who we send</h2>
    </div>
    <div class="grid grid-3" id="guarantees"></div>
  </div>
</section>

<section>
  <div class="wrap narrow">
    <div class="center" style="margin-bottom:26px">
      <p class="eyebrow">Questions</p>
      <h2>Common questions</h2>
    </div>
    <div id="faqList"></div>
  </div>
</section>

<section class="tint">
  <div class="wrap">
    <div class="cta-band">
      <h2>Book your %(name)s cleaning</h2>
      <p>Flat written price in under a minute. No card, no obligation, no salesperson
      calling you back.</p>
      <a class="btn btn-accent btn-lg" href="/book">Get my price</a>
    </div>
    <div class="center" style="margin-top:34px">
      <p class="muted" style="font-size:.92rem">We also clean in
      %(others)s.</p>
    </div>
  </div>
</section>
''' % {
        "name": m["name"],
        "angle": angle,
        "home": ("This is our home base." if m.get("home_base")
                 else "Dispatched daily from our Tampa base."),
        "chips": "".join('<span class="chip">%s</span>' % a for a in areas),
        "sur": ('<p class="hint center" style="margin-top:20px">A drive-time surcharge applies '
                'in %s. It is shown in your quote before you book.</p>'
                % ", ".join(surcharged)) if surcharged else "",
        "others": ", ".join('<a href="/cleaning/%s">%s</a>' % (slug(o["name"]), o["name"])
                            for o in others),
    }

    page("cleaning/%s.html" % s,
         "Cleaning Services in %s, FL | %s" % (m["name"], NAME),
         "House cleaning, deep cleans, move-out and commercial cleaning in %s and %s. "
         "Bonded, insured, background-checked team. Flat upfront pricing."
         % (m["name"], ", ".join(a for a in areas[1:4])),
         body,
         head='<script type="application/ld+json">%s</script>' % schema,
         scripts='<script src="/js/market.js"></script>')


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
