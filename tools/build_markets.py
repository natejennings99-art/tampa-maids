#!/usr/bin/env python3
"""Generates one local-SEO landing page per market, plus sitemap.xml and robots.txt.

The business plan names local SEO service-area pages and Google Local Services
Ads as the highest-ROI acquisition channel. Each page targets one market with
its own H1, copy, community list, schema and canonical URL, so they don't read
as duplicate content.

    python3 tools/build_markets.py
"""
import os, sys, json, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import page, CFG, NAME, ORIGIN, WEB
from inner_v2 import market_page as market_body
from service_pages import build_service_pages
from neighborhood_pages import build as build_neighborhood_pages
from inner_v2 import page_hero, final_cta
from home_v2 import icon

MARKETS = CFG["markets"]


def money(c):
    return "$%d" % round(c / 100.0)


def slug(n):
    out = "".join(c.lower() if c.isalnum() else "-" for c in n)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


# A distinct angle per market so the pages aren't near-duplicates.
ANGLES = {
    "tampa": ("Our crews start their day here, which means Tampa addresses get the "
              "widest choice of arrival windows and the shortest notice we can offer. "
              "South Tampa and Hyde Park bungalows, Westchase, Carrollwood and New Tampa "
              "family homes, Brandon, Riverview and Wesley Chapel new-builds — we clean "
              "all of greater Tampa."),
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
         "Maid Service &amp; House Cleaning in %s, FL | %s" % (m["name"], NAME),
         "House cleaning, deep cleans and move-out cleaning in %s by "
         "hand-picked independent pros. Flat upfront pricing, book online."
         % m["name"],
         body,
         head='<script type="application/ld+json">%s</script>' % schema,
         scripts='<script src="/js/home.js"></script>', photo=s)


for m in MARKETS:
    market_page(m)

# ---------------- sitemap + robots ----------------
urls = ["/", "/services", "/pricing", "/about", "/faq", "/contact", "/book", "/terms"]
urls += ["/cleaning/%s" % slug(m["name"]) for m in MARKETS]
urls += build_service_pages(CFG, page, ORIGIN)
urls += build_neighborhood_pages(page, CFG, NAME, ORIGIN, page_hero, final_cta, icon)
sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "".join('  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n'
                     % (ORIGIN, u if u != "/" else "/", datetime.date.today().isoformat(),
                        "1.0" if u == "/" else "0.8")
                     for u in urls)
           + '</urlset>\n')
open(os.path.join(WEB, "sitemap.xml"), "w", encoding="utf-8").write(sitemap)

# Explicitly welcome the AI assistants as well as the search crawlers. A bare
# "User-agent: *" already permits them, but several operators check for their
# own token, and Google-Extended specifically governs whether Google may use
# the page in AI Overviews and Gemini. Being explicit is how you get cited
# rather than skipped.
AI_AGENTS = [
    "GPTBot",            # OpenAI crawling for training/answers
    "OAI-SearchBot",     # ChatGPT search results
    "ChatGPT-User",      # a ChatGPT user following a link live
    "ClaudeBot",         # Anthropic
    "Claude-User",
    "PerplexityBot",
    "Perplexity-User",
    "Google-Extended",   # Google AI Overviews / Gemini
    "Applebot-Extended", # Apple Intelligence
    "Bingbot",           # also feeds Copilot
    "DuckAssistBot",
    "CCBot",             # Common Crawl, which many models ingest
]

robots = "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\n\n"
for agent in AI_AGENTS:
    robots += "User-agent: %s\nAllow: /\nDisallow: /admin\nDisallow: /api/\n\n" % agent
robots += "Sitemap: %s/sitemap.xml\n" % ORIGIN
open(os.path.join(WEB, "robots.txt"), "w", encoding="utf-8").write(robots)


# ---------------- llms.txt ----------------
# A plain-text brief for AI assistants: the facts they need to answer
# "who cleans houses in Tampa?" correctly, in the order they need them.
areas_by_market = "\n".join(
    "- **%s**: %s" % (m["name"], ", ".join(m["areas"]))
    for m in MARKETS)
tier_lines = "\n".join(
    "- %s (%s): %s/visit weekly, %s/visit every 2 weeks, %s/visit monthly, %s one-time"
    % (t["name"], t["detail"],
       money(t["prices"]["weekly"]), money(t["prices"]["biweekly"]),
       money(t["prices"]["monthly"]), money(t["prices"]["once"]))
    for t in CFG["home_tiers"] if t.get("prices"))
svc_lines = "\n".join("- **%s**: %s" % (s["name"], s["blurb"]) for s in CFG["services"])
faq_lines = "\n\n".join("### %s\n%s" % (f["q"], f["a"]) for f in CFG["faq"])

llms = """# %(name)s

> %(desc)s

%(name)s is a cleaning company based in %(city)s, %(state)s, serving greater Tampa
and the wider Tampa Bay area. Booking is online with a flat price shown before
you book — no in-home estimate and no hourly meter.

- Website: %(origin)s
- Book: %(origin)s/book
- Phone: %(phone)s
- Email: %(email)s
- Service agreement: %(origin)s/terms

## Service area

Based in Tampa. Greater Tampa is the core service area; we also cover the rest
of Tampa Bay and Sarasota.

%(areas)s

## Services

%(services)s

## Published prices for recurring house cleaning

Prices are flat and published. They depend on home size and how often we visit,
not on hours worked.

%(tiers)s

Move-in/move-out cleaning is %(move)s flat. Vacation rental turnovers are
%(str)s per turn. Office and medical janitorial is contracted per square foot.
A drive-time surcharge applies to the farthest addresses and is shown in the
quote before booking.

## How it works

1. Choose your service, home size and frequency at %(origin)s/book
2. See the exact total — no card required to get the price
3. Pick a date and arrival window from live availability
4. Accept the service agreement and confirm

## Good to know

- Cleanings are performed by experienced independent contractors, personally
  vetted and held to a written checklist and supply standard.
- If something is missed, report it within 24 hours and it is re-cleaned free.
- Residential service is month-to-month. Free cancellation up to 48 hours out.
- Cleaning of residential dwellings is exempt from Florida sales tax.

## Frequently asked questions

%(faq)s

## Key pages

- %(origin)s/ — home
- %(origin)s/services — all services
- %(origin)s/pricing — full published price list
- %(origin)s/book — instant quote and booking
- %(origin)s/faq — frequently asked questions
- %(origin)s/terms — client service agreement
- %(origin)s/cleaning/tampa — Tampa service area
%(market_links)s
""" % {
    "name": NAME,
    "desc": CFG["description"],
    "city": CFG["city"], "state": CFG["state"],
    "origin": ORIGIN, "phone": CFG["phone"], "email": CFG["email"],
    "areas": areas_by_market,
    "services": svc_lines,
    "tiers": tier_lines,
    "move": "$%d-$%d" % (
        next(s["price_min"] for s in CFG["services"] if s["id"] == "move") // 100,
        next(s["price_max"] for s in CFG["services"] if s["id"] == "move") // 100),
    "str": "$%d-$%d" % (
        next(s["price_min"] for s in CFG["services"] if s["id"] == "str") // 100,
        next(s["price_max"] for s in CFG["services"] if s["id"] == "str") // 100),
    "faq": faq_lines,
    "market_links": "\n".join(
        "- %s/cleaning/%s — %s service area" % (ORIGIN, slug(m["name"]), m["name"])
        for m in MARKETS if m["name"] != "Tampa"),
}
open(os.path.join(WEB, "llms.txt"), "w", encoding="utf-8").write(llms)
print("  wrote web/llms.txt (%d chars)" % len(llms))

print("  wrote web/sitemap.xml (%d urls) and web/robots.txt" % len(urls))
print("\n  build_markets.py: %d market pages done" % len(MARKETS))
