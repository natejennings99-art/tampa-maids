#!/usr/bin/env python3
"""Assembles the static marketing pages from one shared shell.

Output is plain HTML in web/ with no runtime build step — you can hand-edit the
generated files afterwards. Re-run this only if you want to change the header,
footer, or page chrome in one place:  python3 tools/build_site.py
"""
import os, json
from home_v2 import PHOTOS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
CFG = json.load(open(os.path.join(ROOT, "business.json"), encoding="utf-8"))
NAME = CFG["name"]
MARKETS = [m["name"] for m in CFG.get("markets", [])]
MARKET_LINE = ", ".join(MARKETS[:-1]) + " and " + MARKETS[-1] if MARKETS else ""

LOGO = '''<svg viewBox="0 0 40 40" aria-hidden="true">
  <rect width="40" height="40" rx="10" fill="#0c4a5c"/>
  <path d="M11 33V19.5a9 9 0 0 1 18 0V33z" fill="#f7f3ec"/>
  <path d="M14.2 33a5.8 5.8 0 0 1 11.6 0z" fill="#e39b36"/>
  <path d="M20 14.6l1.4 3.4 3.4 1.4-3.4 1.4-1.4 3.4-1.4-3.4-3.4-1.4 3.4-1.4z" fill="#0c4a5c"/>
</svg>'''
WORD = NAME.replace(" Cleaning", "")
LOCKUP = LOGO + '<span class="logo-word"><b>%s</b><small>Cleaning Co.</small></span>' % WORD

NAV = [("/", "Home"), ("/services", "Services"), ("/pricing", "Pricing"),
       ("/about", "About"), ("/faq", "FAQ"), ("/contact", "Contact")]

HEADER = '''<header class="site-header">
  <div class="wrap">
    <a class="logo" href="/" aria-label="%s home">%s</a>
    <button class="menu-btn" aria-label="Menu" aria-expanded="false"><span></span></button>
    <nav class="nav">%s</nav>
    <div class="header-cta">
      <a class="header-phone" data-biz-href="phone" href="tel:%s" data-biz="phone">%s</a>
      <a class="btn btn-primary btn-sm" href="/book">Book now</a>
    </div>
  </div>
</header>''' % (NAME, LOCKUP,
                "".join('<a href="%s">%s</a>' % (h, t) for h, t in NAV),
                CFG["phone_raw"], CFG["phone"])

FOOTER = '''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <div class="logo">%s</div>
        <p style="max-width:34ch">%s</p>
        <p style="font-size:.84rem;opacity:.75">%s</p>
      </div>
      <div>
        <h2>Services</h2>
        <a href="/services/house-cleaning-tampa">House Cleaning</a>
        <a href="/services/deep-cleaning-tampa">Deep Cleaning</a>
        <a href="/services/move-out-cleaning-tampa">Move In / Move Out</a>
        <a href="/services/airbnb-cleaning-tampa">Vacation Rentals</a>
        <a href="/services/office-cleaning-tampa">Office &amp; Medical</a>
        <a href="/services/post-construction-cleaning-tampa">Post-Construction</a>
      </div>
      <div>
        <h2>Service areas</h2>
        %s
      </div>
      <div>
        <h2>Company</h2>
        <a href="/about">About us</a>
        <a href="/pricing">Pricing</a>
        <a href="/faq">FAQ</a>
        <a href="/contact">Contact</a>
        <a href="/track">Track a booking</a>
        <a href="/terms">Service agreement</a>
        <a href="/app">Phone app</a>
      </div>
      <div>
        <h2>Get in touch</h2>
        <a data-biz-href="phone" href="tel:%s" data-biz="phone">%s</a>
        <a data-biz-href="email" href="mailto:%s" data-biz="email">%s</a>
        <p style="margin-top:14px;font-size:.85rem;opacity:.8">Serving %s, plus the communities around each.</p>
        <a class="btn btn-accent btn-sm" style="margin-top:12px;display:inline-flex" href="/book">Get a free quote</a>
      </div>
    </div>
    <div class="footer-bottom">
      <div>&copy; <span id="yr"></span> %s. All rights reserved.</div>
      <div>%s</div>
    </div>
  </div>
</footer>
<script>document.getElementById('yr').textContent=new Date().getFullYear()</script>''' % (
    LOCKUP, CFG["description"], CFG["license"],
    "".join('<a href="/cleaning/%s">Cleaning in %s</a>'
            % ("".join(c.lower() if c.isalnum() else "-" for c in m["name"])
               .replace("--", "-").strip("-"), m["name"])
            for m in CFG.get("markets", [])),
    CFG["phone_raw"], CFG["phone"], CFG["email"], CFG["email"],
    MARKET_LINE, NAME, CFG["legal"])

# Search Console / Bing Webmaster ownership proof. Set seo.google_site_verification
# (and optionally seo.bing_site_verification) in business.json and every page
# carries the tag -- which is the point, since the verification method Google
# offers varies and a token is worthless if it only lands on the homepage.
def _verify_tags(cfg):
    seo = cfg.get("seo") or {}
    out = []
    for key, name in (("google_site_verification", "google-site-verification"),
                      ("bing_site_verification", "msvalidate.01")):
        tok = (seo.get(key) or "").strip()
        if tok:
            out.append('\n<meta name="%s" content="%s">' % (name, tok))
    return "".join(out)


VERIFY = _verify_tags(CFG)

def _offer_bar(cfg):
    """A slim offer strip above the header.

    The intro offer was configured from the start and rendered on /pricing
    alone -- one page out of forty-seven -- while being the hook in every piece
    of outreach. Someone arriving on a city page from a Facebook comment never
    saw it.

    It names the biweekly condition, because an offer that only applies to one
    plan and does not say so is the kind of thing a customer discovers at
    checkout and resents.
    """
    io = (cfg.get("pricing") or {}).get("intro_offer") or {}
    if not io.get("label"):
        return ""
    freq = next((f["name"] for f in cfg.get("frequencies", [])
                 if f["id"] == io.get("requires")), "")
    cond = (' on the &ldquo;%s&rdquo; plan' % freq) if freq else ""
    return ('<div class="offer-bar"><div class="wrap">'
            '<span class="offer-bar-label">New client offer</span> '
            '<strong>%s</strong>%s &mdash; '
            '<a href="/book">see your price</a></div></div>'
            % (io["label"], cond))


OFFER_BAR = _offer_bar(CFG)


SHELL = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#0c4a5c">{verify}
<link rel="icon" href="/icons/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icons/icon-180.png">
<link rel="canonical" href="{canonical}">
<meta property="og:site_name" content="{sitename}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="/fonts/manrope-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/fraunces-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preconnect" href="https://images.unsplash.com">
<link rel="stylesheet" href="/css/site.css">
<script>document.documentElement.classList.add('js')</script>
{head}
</head>
<body>
{offerbar}
{header}
<main>
{body}
</main>
{footer}
<script src="/js/api.js"></script>
<script src="/js/site.js"></script>
{scripts}
</body>
</html>
'''


ORIGIN = CFG.get("url", "").rstrip("/")


def canonical_for(slug):
    """Pretty canonical URL: index.html -> /, services.html -> /services."""
    if slug == "index.html":
        return ORIGIN + "/"
    return ORIGIN + "/" + slug[:-5] if slug.endswith(".html") else ORIGIN + "/" + slug


def og_image(photo):
    """Link-preview image (Facebook, Nextdoor, texts): a site path such as the branded
    cover, or a 1200x630 JPEG crop of one of the page photos."""
    if photo.startswith("/"):
        return ORIGIN + photo
    return ("https://images.unsplash.com/%s?fit=crop&amp;w=1200&amp;h=630&amp;q=80&amp;fm=jpg"
            % PHOTOS.get(photo, PHOTOS["hero"]))


def page(slug, title, desc, body, head="", scripts="", photo="hero"):
    html = SHELL.format(title=title, desc=desc, body=body, head=head, scripts=scripts,
                        verify=VERIFY, offerbar=OFFER_BAR,
                        og_image=og_image(photo),
                        header=HEADER, footer=FOOTER, sitename=NAME,
                        origin=ORIGIN, canonical=canonical_for(slug))
    path = os.path.join(WEB, slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("  wrote web/%s  (%d KB)" % (slug, len(html) // 1024))


# ---------------------------------------------------------------- home
from home_v2 import build_home
HOME = build_home(CFG)


def _geo():
    """Coordinates from the Google Business Profile, when they're recorded."""
    g = (CFG.get("seo") or {}).get("geo") or {}
    if not (g.get("lat") and g.get("lng")):
        return None
    return {"@type": "GeoCoordinates", "latitude": g["lat"], "longitude": g["lng"]}


def _offer_catalog():
    """Real services at real prices, straight from the price table.

    Published pricing is the whole competitive position -- most Tampa
    competitors answer "how much?" with "call us" -- so it belongs in the
    markup too, not just the visible page. Prices come from business.json so
    the catalogue cannot contradict what the booking form charges.
    """
    items = []
    tiers = [t for t in CFG["home_tiers"] if t.get("prices")]
    if tiers:
        lo = min(t["prices"]["biweekly"] for t in tiers)
        hi = max(t["prices"]["monthly"] for t in tiers)
        items.append(("Recurring House Cleaning", lo, hi,
                      "Weekly, every-two-weeks or monthly cleaning at a flat price per visit."))
        items.append(("Deep Cleaning", min(t["prices"]["once"] for t in tiers),
                      max(t["prices"]["once"] for t in tiers),
                      "A one-time top-to-bottom reset, priced flat before we start."))
    for sid, label in (("move", "Move-In / Move-Out Cleaning"),
                       ("str", "Vacation Rental Turnover"),
                       ("construction", "Post-Construction Cleaning")):
        svc = next((x for x in CFG["services"] if x["id"] == sid), None)
        if svc and svc.get("price_min") and svc.get("price_max"):
            items.append((label, svc["price_min"], svc["price_max"], svc.get("blurb", "")))
    if not items:
        return None
    return {
        "@type": "OfferCatalog",
        "name": "Cleaning services in greater Tampa",
        "itemListElement": [{
            "@type": "Offer",
            "itemOffered": {"@type": "Service", "name": name, "description": desc[:300]},
            "priceSpecification": {
                "@type": "PriceSpecification",
                "minPrice": "%.2f" % (lo / 100.0),
                "maxPrice": "%.2f" % (hi / 100.0),
                "priceCurrency": CFG["pricing"]["currency"],
            },
            "availableAtOrFrom": {"@type": "Place", "address": {
                "@type": "PostalAddress", "addressLocality": CFG["city"],
                "addressRegion": CFG["state"], "addressCountry": "US"}},
        } for name, lo, hi, desc in items],
    }


LOCAL_BUSINESS = json.dumps({
    "@context": "https://schema.org",
    "@type": "HouseCleaningService",
    "name": NAME,
    "url": ORIGIN,
    "image": ORIGIN + "/icons/icon-512.png",
    "logo": ORIGIN + "/icons/logo-1200.png",
    "description": CFG["description"],
    "telephone": CFG["phone"],
    "email": CFG["email"],
    "priceRange": "$$",
    "address": {"@type": "PostalAddress", "addressLocality": CFG["city"],
                "addressRegion": CFG["state"], "addressCountry": "US"},
    "areaServed": [{"@type": "City", "name": c} for c in CFG["service_area"]],
    "openingHours": ["Mo-Sa 08:00-17:00"],
    "sameAs": [v for v in CFG.get("social", {}).values() if v],
    "hasMap": CFG.get("social", {}).get("google") or None,
    "geo": _geo(),
    "hasOfferCatalog": _offer_catalog(),
}, indent=2)

page("index.html",
     "Tampa House Cleaning &amp; Maid Service | %s" % NAME,
     "House cleaning and maid service across greater Tampa, from South Tampa to Brandon, Wesley Chapel, St. Pete and Clearwater. Flat prices, book in a minute.", HOME,
     head='<script type="application/ld+json">%s</script>' % LOCAL_BUSINESS,
     scripts='<script src="/js/home.js"></script>', photo="/icons/og-cover.jpg")

# ---------------------------------------------------------------- services & pricing
from inner_v2 import services_page, pricing_page

page("services.html", "Cleaning Services in Tampa Bay | %s" % NAME,
     "House cleaning, deep cleans, move-out, Airbnb turnovers, office and post-construction "
     "cleaning across greater Tampa, St. Pete and Clearwater.",
     services_page(CFG), scripts='<script src="/js/home.js"></script>', photo="deep")

page("pricing.html", "House Cleaning Prices in Tampa | %s" % NAME,
     "Published flat-rate house cleaning prices for greater Tampa homes. Weekly, "
     "bi-weekly, monthly and one-time rates by home size. No hourly meter.",
     pricing_page(CFG), scripts='<script src="/js/home.js"></script>')

print("\n  build_site.py: marketing pages done")
