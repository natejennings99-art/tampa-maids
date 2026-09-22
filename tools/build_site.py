#!/usr/bin/env python3
"""Assembles the static marketing pages from one shared shell.

Output is plain HTML in web/ with no runtime build step — you can hand-edit the
generated files afterwards. Re-run this only if you want to change the header,
footer, or page chrome in one place:  python3 tools/build_site.py
"""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
CFG = json.load(open(os.path.join(ROOT, "business.json"), encoding="utf-8"))
NAME = CFG["name"]
MARKETS = [m["name"] for m in CFG.get("markets", [])]
MARKET_LINE = ", ".join(MARKETS[:-1]) + " and " + MARKETS[-1] if MARKETS else ""

LOGO = '''<svg viewBox="0 0 40 40" fill="none" aria-hidden="true">
  <rect width="40" height="40" rx="11" fill="#0b6e8f"/>
  <path d="M7 26c3.2 0 3.2-3 6.4-3s3.2 3 6.4 3 3.2-3 6.4-3 3.2 3 6.4 3" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>
  <path d="M7 31c3.2 0 3.2-2.4 6.4-2.4S16.6 31 19.8 31s3.2-2.4 6.4-2.4S29.4 31 32.6 31" stroke="#7fd0e8" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M20 8.5l1.9 4.4 4.4 1.9-4.4 1.9L20 21.1l-1.9-4.4-4.4-1.9 4.4-1.9z" fill="#f2a541"/>
</svg>'''

NAV = [("/", "Home"), ("/services", "Services"), ("/pricing", "Pricing"),
       ("/about", "About"), ("/faq", "FAQ"), ("/contact", "Contact")]

HEADER = '''<header class="site-header">
  <div class="wrap">
    <a class="logo" href="/">%s<span>%s</span></a>
    <button class="menu-btn" aria-label="Menu" aria-expanded="false"><span></span></button>
    <nav class="nav">%s</nav>
    <div class="header-cta">
      <a class="header-phone" data-biz-href="phone" href="tel:%s" data-biz="phone">%s</a>
      <a class="btn btn-primary btn-sm" href="/book">Book now</a>
    </div>
  </div>
</header>''' % (LOGO, NAME,
                "".join('<a href="%s">%s</a>' % (h, t) for h, t in NAV),
                CFG["phone_raw"], CFG["phone"])

FOOTER = '''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <div class="logo">%s<span>%s</span></div>
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
    LOGO, NAME, CFG["description"], CFG["license"],
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
<meta name="theme-color" content="#0b6e8f">
<link rel="icon" href="/icons/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icons/icon-180.png">
<link rel="canonical" href="{canonical}">
<meta property="og:site_name" content="{sitename}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{origin}/icons/icon-512.png">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/site.css">
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


def page(slug, title, desc, body, head="", scripts=""):
    html = SHELL.format(title=title, desc=desc, body=body, head=head, scripts=scripts,
                        header=HEADER, footer=FOOTER, sitename=NAME,
                        origin=ORIGIN, canonical=canonical_for(slug))
    path = os.path.join(WEB, slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("  wrote web/%s  (%d KB)" % (slug, len(html) // 1024))


# ---------------------------------------------------------------- home
HOME = '''
<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">Tampa &middot; St. Petersburg &middot; Clearwater &middot; Sarasota</p>
      <h1>Get your time back.<br><em>We'll handle the rest.</em></h1>
      <p class="lede">Bonded, insured, background-checked cleaners who show up on time,
      use safer products, and leave your space noticeably better &mdash; every single visit.</p>
      <ul class="hero-points" id="heroPoints"></ul>
      <div class="btn-row">
        <a class="btn btn-primary btn-lg" href="/book">See your price in 60 seconds</a>
        <a class="btn btn-ghost btn-lg" data-biz-href="phone" href="#">Call us</a>
      </div>
      <div class="trustline">
        <span class="stars">&#9733;&#9733;&#9733;&#9733;&#9733;</span>
        <span>Loved by Tampa Bay families and businesses</span>
        <span aria-hidden="true">&middot;</span>
        <span>Licensed &amp; insured</span>
      </div>
    </div>
    <div class="quote-card" id="heroQuote"></div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="center" style="margin-bottom:44px">
      <p class="eyebrow">What we do</p>
      <h2>One team for every kind of clean</h2>
      <p class="lede">From a bi-weekly tidy to a nightly medical suite. Same standards, same people, same guarantee.</p>
    </div>
    <div class="grid grid-3" id="svcGrid"></div>
  </div>
</section>

<section class="tint">
  <div class="wrap">
    <div class="center" style="margin-bottom:44px">
      <p class="eyebrow">Why us</p>
      <h2>The difference is who we send</h2>
      <p class="lede">Most cleaning "companies" in Tampa Bay are gig platforms sending whoever
      accepted the job. We're not that.</p>
    </div>
    <div class="grid grid-3" id="guarantees"></div>
  </div>
</section>

<section class="dark">
  <div class="wrap">
    <div class="center" style="margin-bottom:48px">
      <p class="eyebrow">How it works</p>
      <h2>Booked in about a minute</h2>
    </div>
    <div class="steps">
      <div class="step"><div class="step-n">1</div>
        <h3>Tell us about your place</h3>
        <p>Home size, how often, any extras. Takes under a minute &mdash; no phone tag,
        no in-home estimate needed.</p></div>
      <div class="step"><div class="step-n">2</div>
        <h3>See your exact price</h3>
        <p>A flat, written total before you book. Not an hourly meter, not a "starting at."
        The price you see is the price you pay.</p></div>
      <div class="step"><div class="step-n">3</div>
        <h3>Pick a time and relax</h3>
        <p>We text you when the crew is on the way, and upload before-and-after photos
        to your account when they finish.</p></div>
    </div>
    <div class="center" style="margin-top:44px">
      <a class="btn btn-accent btn-lg" href="/book">Start my free quote</a>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="center" style="margin-bottom:44px">
      <p class="eyebrow">Reviews</p>
      <h2>What Tampa Bay says</h2>
    </div>
    <div class="grid grid-3" id="testimonials"></div>
  </div>
</section>

<section class="tint-teal">
  <div class="wrap">
    <div class="center" style="margin-bottom:38px">
      <p class="eyebrow">Service area</p>
      <h2>Four markets, one team</h2>
      <p class="lede" id="areaNote" style="margin-inline:auto"></p>
    </div>
    <div class="grid grid-4" id="marketGrid"></div>
    <p class="muted center" style="margin-top:28px;font-size:.92rem">Just outside these?
      <a data-biz-href="phone" href="#">Give us a call</a> &mdash; we can often still make it work.</p>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="cta-band">
      <h2>Your first clean could be this week</h2>
      <p>Get a flat, written price in under a minute. No card required, no obligation,
      and no salesperson calling you back.</p>
      <div class="btn-row" style="justify-content:center">
        <a class="btn btn-accent btn-lg" href="/book">Get my price</a>
        <a class="btn btn-white btn-lg" data-biz-href="phone" href="#">Call instead</a>
      </div>
    </div>
  </div>
</section>
'''

LOCAL_BUSINESS = json.dumps({
    "@context": "https://schema.org",
    "@type": "HouseCleaningService",
    "name": NAME,
    "url": ORIGIN,
    "image": ORIGIN + "/icons/icon-512.png",
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
     "Bonded, insured house and office cleaning in Tampa, St. Pete, Clearwater and Sarasota. Flat upfront pricing, background-checked team. Book online.", HOME,
     head='<script type="application/ld+json">%s</script>' % LOCAL_BUSINESS,
     scripts='<script src="/js/home.js"></script>')

# ---------------------------------------------------------------- services
SERVICES = '''
<section style="background:linear-gradient(170deg,var(--teal-50),#fff);padding-bottom:40px">
  <div class="wrap narrow center">
    <p class="eyebrow">Services</p>
    <h1>Every kind of clean, one accountable team</h1>
    <p class="lede" style="margin-inline:auto">Residential, vacation rental, and commercial
    cleaning across Tampa, St. Petersburg, Clearwater and Sarasota. Every service below is performed by our own W-2 employees,
    to a written checklist, with photo verification.</p>
  </div>
</section>
<section style="padding-top:40px"><div class="wrap"><div id="svcDetail"></div></div></section>
<section class="tint">
  <div class="wrap">
    <div class="center" style="margin-bottom:40px">
      <p class="eyebrow">Add-ons</p>
      <h2>Extras you can add to any visit</h2>
      <p class="lede">Add these when you book, or ask the crew on the day &mdash;
      we'll re-quote before we start, never after.</p>
    </div>
    <div class="grid grid-4" id="addonGrid"></div>
  </div>
</section>
<section><div class="wrap"><div class="cta-band">
  <h2>Not sure which one you need?</h2>
  <p>Answer four questions and we'll show you the right service and an exact price.</p>
  <a class="btn btn-accent btn-lg" href="/book">Find my price</a>
</div></div></section>
'''
page("services.html", "Cleaning Services in Tampa Bay | %s" % NAME,
     "House cleaning, deep cleans, move-out, vacation rental turnovers, office and medical "
     "janitorial, and post-construction cleaning across Tampa, St. Petersburg, Clearwater "
     "and Sarasota.",
     SERVICES, scripts='<script src="/js/services.js"></script>')

# ---------------------------------------------------------------- pricing
PRICING = '''
<section style="background:linear-gradient(170deg,var(--teal-50),#fff);padding-bottom:40px">
  <div class="wrap narrow center">
    <p class="eyebrow">Pricing</p>
    <h1>Flat prices, published openly</h1>
    <p class="lede" style="margin-inline:auto">No hourly meter, no "starting at," no estimate
    that changes at the door. Here is what we charge.</p>
  </div>
</section>

<section style="padding-top:44px">
  <div class="wrap">
    <h2>Recurring house cleaning</h2>
    <p class="lede">Priced by home size and how often we visit. Bi-weekly is our most popular plan.</p>
    <div class="table-scroll" style="margin:26px 0 14px"><table class="ptable" id="tierTable"></table></div>
    <p class="hint" id="firstNote"></p>
  </div>
</section>

<section class="tint">
  <div class="wrap">
    <h2>One-time and specialty cleaning</h2>
    <p class="lede">Flat rates quoted on square footage and condition.</p>
    <div class="grid grid-3" style="margin-top:26px" id="flatGrid"></div>
  </div>
</section>

<section>
  <div class="wrap">
    <h2>Commercial &amp; janitorial</h2>
    <p class="lede">Contracted, per-square-foot pricing for offices, medical suites and retail.</p>
    <div class="table-scroll" style="margin:26px 0"><table class="ptable" id="commTable"></table></div>
    <p class="hint" id="commNote"></p>
  </div>
</section>

<section class="tint-teal">
  <div class="wrap">
    <h2 class="center">What's always included</h2>
    <div class="grid grid-4" style="margin-top:34px" id="incGrid"></div>
  </div>
</section>

<section><div class="wrap"><div class="cta-band">
  <h2>See your exact number</h2>
  <p>The calculator uses the same table above. No email required to see your price.</p>
  <a class="btn btn-accent btn-lg" href="/book">Calculate my price</a>
</div></div></section>
'''
page("pricing.html", "Cleaning Prices in Tampa Bay &amp; Sarasota | %s" % NAME,
     "Published flat-rate cleaning prices for Tampa Bay and Sarasota homes. Weekly, "
     "bi-weekly, monthly and one-time rates by home size. No hourly meter.",
     PRICING, scripts='<script src="/js/pricing.js"></script>')

print("\n  build_site.py: marketing pages done")
