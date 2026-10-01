#!/usr/bin/env python3
"""Second half of the page build: about, faq, contact, book, track, 404.
Shares the shell defined in build_site.py.  python3 tools/build_site2.py"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import page, CFG, NAME
from inner_v2 import about_page, faq_page, contact_page, terms_page

# ---------------------------------------------------------------- about
page("about.html", "About %s | Locally Owned in Tampa" % NAME,
     "Locally owned cleaning company serving Tampa, St. Petersburg, Clearwater and Sarasota "
     "with hand-picked independent cleaning pros.",
     about_page(CFG), scripts='<script src="/js/home.js"></script>', photo="about")

# ---------------------------------------------------------------- faq
FAQ_SCHEMA = json.dumps({
    "@context": "https://schema.org", "@type": "FAQPage",
    "mainEntity": [{"@type": "Question", "name": f["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                   for f in CFG["faq"]],
}, indent=2)

page("faq.html", "House Cleaning FAQ | %s" % NAME,
     "Answers about pricing, insurance, supplies, cancellations, recurring crews and "
     "service areas for Tampa, St. Pete, Clearwater and Sarasota cleaning.",
     faq_page(CFG), head='<script type="application/ld+json">%s</script>' % FAQ_SCHEMA,
     scripts='<script src="/js/home.js"></script>')

# ---------------------------------------------------------------- contact
page("contact.html", "Contact Us | %s, Tampa FL" % NAME,
     "Call, text or message Tampa Maids Cleaning for a house or office cleaning quote anywhere in greater Tampa. A real person replies within one business day.",
     contact_page(CFG), scripts='<script src="/js/home.js"></script><script src="/js/contact.js"></script>')

# ---------------------------------------------------------------- track
TRACK = '''
<section class="p-hero p-hero-c p-hero-sm">
  <div class="wrap">
    <p class="h-kicker">Your booking</p>
    <h1>Track a <em>booking.</em></h1>
    <p class="lede">Enter the reference from your confirmation and the email you booked with.</p>
  </div>
</section>
<section style="padding-top:30px">
  <div class="wrap narrow">
    <form id="trackForm" class="card" novalidate>
      <div id="trackMsg"></div>
      <div class="field-row">
        <div class="field"><label for="tf-ref">Booking reference *</label>
          <input id="tf-ref" type="text" placeholder="%s-XXXXXX" required
            style="text-transform:uppercase"></div>
        <div class="field"><label for="tf-email">Email *</label>
          <input id="tf-email" type="email" autocomplete="email" required></div>
      </div>
      <button class="btn btn-primary" type="submit" id="tfBtn">Find my booking</button>
    </form>
    <div id="trackResult" style="margin-top:26px"></div>
    <p class="hint center" style="margin-top:24px">Prefer an app?
      <a href="/app">Install our phone app</a> to see all your cleans in one place.</p>
  </div>
</section>
'''
TRACK = TRACK % CFG["booking"].get("ref_prefix", "TM")

page("track.html", "Track your booking | %s" % NAME,
     "Look up, reschedule or cancel your cleaning appointment.",
     TRACK, head='<meta name="robots" content="noindex">',
     scripts='<script src="/js/track.js"></script>')

# ---------------------------------------------------------------- 404
NF = '''
<section class="p-hero p-hero-c" style="padding:110px 0 120px">
  <div class="wrap">
    <p class="h-kicker">404</p>
    <h1>That page got <em>cleaned up.</em></h1>
    <p class="lede">The link is broken or the page has moved. Here's where most people are headed:</p>
    <div class="h-cta">
      <a class="btn btn-primary btn-lg" href="/book">Get my instant price</a>
      <a class="btn btn-ghost btn-lg" href="/services">Services</a>
      <a class="btn btn-ghost btn-lg" href="/">Home</a>
    </div>
  </div>
</section>
'''
page("terms.html", "Service Agreement | %s" % NAME,
     "The terms you agree to when you book a cleaning with Tampa Maids Cleaning: scope, "
     "pricing, cancellation, access, damage reporting and our 24-hour re-clean guarantee.",
     terms_page(CFG))

page("404.html", "Page not found | %s" % NAME, "Page not found.", NF)

print("\n  build_site2.py: remaining pages done")
