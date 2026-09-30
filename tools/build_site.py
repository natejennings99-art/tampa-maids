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
        <h4>Services</h4>
        <a href="/services#residential">House Cleaning</a>
        <a href="/services#deep">Deep Cleaning</a>
        <a href="/services#move">Move In / Move Out</a>
        <a href="/services#str">Vacation Rentals</a>
        <a href="/services#commercial">Office &amp; Medical</a>
        <a href="/services#construction">Post-Construction</a>
      </div>
      <div>
        <h4>Service areas</h4>
        %s
      </div>
      <div>
        <h4>Company</h4>
        <a href="/about">About us</a>
        <a href="/pricing">Pricing</a>
        <a href="/faq">FAQ</a>
        <a href="/contact">Contact</a>
        <a href="/track">Track a booking</a>
        <a href="/app">Phone app</a>
      </div>
      <div>
        <h4>Get in touch</h4>
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

SHELL = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#0c4a5c">
<link rel="icon" href="/icons/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icons/icon-180.png">
<link rel="canonical" href="{canonical}">
<meta property="og:site_name" content="{sitename}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/site.css">
<script>document.documentElement.classList.add('js')</script>
{head}
</head>
<body>
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
    """1200x630 JPEG crop of a page photo for link previews (Facebook, Nextdoor, texts)."""
    return ("https://images.unsplash.com/%s?fit=crop&amp;w=1200&amp;h=630&amp;q=80&amp;fm=jpg"
            % PHOTOS.get(photo, PHOTOS["hero"]))


def page(slug, title, desc, body, head="", scripts="", photo="hero"):
    html = SHELL.format(title=title, desc=desc, body=body, head=head, scripts=scripts,
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
}, indent=2)

page("index.html",
     "House Cleaning Tampa, St. Pete &amp; Clearwater | %s" % NAME,
     "House and office cleaning in Tampa, St. Pete, Clearwater and Sarasota by a background-checked W-2 team. Flat upfront pricing. Book online in about a minute.", HOME,
     head='<script type="application/ld+json">%s</script>' % LOCAL_BUSINESS,
     scripts='<script src="/js/home.js"></script>')

# ---------------------------------------------------------------- services & pricing
from inner_v2 import services_page, pricing_page

page("services.html", "Cleaning Services in Tampa Bay | %s" % NAME,
     "House cleaning, deep cleans, move-out, vacation rental turnovers, office and medical "
     "janitorial, and post-construction cleaning across Tampa, St. Petersburg, Clearwater "
     "and Sarasota.",
     services_page(CFG), scripts='<script src="/js/home.js"></script>', photo="deep")

page("pricing.html", "Cleaning Prices in Tampa Bay &amp; Sarasota | %s" % NAME,
     "Published flat-rate cleaning prices for Tampa Bay and Sarasota homes. Weekly, "
     "bi-weekly, monthly and one-time rates by home size. No hourly meter.",
     pricing_page(CFG), scripts='<script src="/js/home.js"></script>')

print("\n  build_site.py: marketing pages done")
