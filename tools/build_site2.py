#!/usr/bin/env python3
"""Second half of the page build: about, faq, contact, book, track, 404.
Shares the shell defined in build_site.py.  python3 tools/build_site2.py"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import page, CFG, NAME

# ---------------------------------------------------------------- about
ABOUT = '''
<section style="background:linear-gradient(170deg,var(--teal-50),#fff);padding-bottom:36px">
  <div class="wrap narrow">
    <p class="eyebrow">About us</p>
    <h1>Locally owned. Personally accountable.</h1>
    <p class="lede" id="mission"></p>
  </div>
</section>

<section style="padding-top:36px">
  <div class="wrap">
    <div class="grid grid-2" style="gap:48px;align-items:start">
      <div>
        <h2>Why we started</h2>
        <p>Tampa Bay has no shortage of cleaning companies. What it has a shortage of is
        cleaning companies you can count on twice in a row.</p>
        <p>The national franchises are consistent but rigid, expensive, and impersonal &mdash;
        you get a different pair of strangers each visit and a price set in another state.
        The gig apps are cheap and instant, but there is no vetting, no recourse, and no
        chance of the same person coming back. And the small independents, many of them
        excellent, are one bad week away from missing your appointment entirely.</p>
        <p>We built <span data-biz="name"></span> in the gap between them: franchise-level
        systems and reliability, at an independent's price, run by someone who lives here
        and answers the phone.</p>
        <h2 style="margin-top:36px">How we're different</h2>
        <p>Everyone who enters your home is our <strong>W-2 employee</strong> &mdash; not a
        contractor, not a gig worker. They are background-checked and E-Verified before their
        first job, badged, uniformed, paid above market with paid drive time, and trained
        over three weeks before they work unsupervised.</p>
        <p>That costs us more. It is also the entire reason our clients stay: the same two
        people show up, they already know your house, and if anything goes wrong there is a
        company standing behind it with a $1M/$2M policy and a $25,000 bond.</p>
      </div>
      <aside>
        <div class="card" style="background:var(--sand);border:0">
          <h3>At a glance</h3>
          <div id="glance"></div>
        </div>
        <div class="card" style="margin-top:20px">
          <h3>Our promise</h3>
          <p>If something isn't right, tell us within 24 hours and we re-clean it free.
          No forms, no argument. We call it the rescue protocol and it has never been
          a hard conversation.</p>
        </div>
      </aside>
    </div>
  </div>
</section>

<section class="tint">
  <div class="wrap">
    <div class="center" style="margin-bottom:40px">
      <p class="eyebrow">What we stand for</p>
      <h2>Four things we don't compromise on</h2>
    </div>
    <div class="grid grid-4" id="values"></div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="center" style="margin-bottom:40px">
      <p class="eyebrow">Who we serve</p>
      <h2>Homes, rentals and businesses</h2>
    </div>
    <div class="table-scroll"><table class="ptable" id="segTable"></table></div>
  </div>
</section>

<section class="dark">
  <div class="wrap narrow center">
    <p class="eyebrow">Our standard</p>
    <h2>Every job runs on a written checklist</h2>
    <p class="lede">A 37-point residential checklist. A 28-point vacation-rental turnover
    checklist. A medical checklist aligned to CDC surface-disinfection guidance. Crews tick
    each item off in our app as they go, and you can see the result.</p>
    <a class="btn btn-accent btn-lg" href="/book" style="margin-top:18px">Book your first clean</a>
  </div>
</section>
'''
page("about.html", "About %s | Tampa, St. Pete, Clearwater &amp; Sarasota" % NAME,
     "Locally owned, bonded and insured cleaning company serving Tampa, St. Petersburg, "
     "Clearwater and Sarasota with a background-checked W-2 team.",
     ABOUT, scripts='<script src="/js/about.js"></script>')

# ---------------------------------------------------------------- faq
FAQ = '''
<section style="background:linear-gradient(170deg,var(--teal-50),#fff);padding-bottom:36px">
  <div class="wrap narrow center">
    <p class="eyebrow">Questions</p>
    <h1>Everything people ask us</h1>
    <p class="lede" style="margin-inline:auto">If your question isn't here,
    <a data-biz-href="phone" href="#">call us</a> or
    <a href="/contact">send a message</a> &mdash; a real person replies.</p>
  </div>
</section>
<section style="padding-top:30px"><div class="wrap narrow"><div id="faqList"></div></div></section>
<section class="tint"><div class="wrap"><div class="cta-band">
  <h2>Still deciding?</h2>
  <p>Seeing your actual price usually settles it. It takes under a minute and needs no card.</p>
  <a class="btn btn-accent btn-lg" href="/book">Show me my price</a>
</div></div></section>
'''
FAQ_SCHEMA = json.dumps({
    "@context": "https://schema.org", "@type": "FAQPage",
    "mainEntity": [{"@type": "Question", "name": f["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                   for f in CFG["faq"]],
}, indent=2)

page("faq.html", "Cleaning FAQ | %s" % NAME,
     "Answers about pricing, insurance, supplies, cancellations, recurring crews and "
     "service areas for Tampa, St. Pete, Clearwater and Sarasota cleaning.",
     FAQ, head='<script type="application/ld+json">%s</script>' % FAQ_SCHEMA,
     scripts='<script src="/js/faq.js"></script>')

# ---------------------------------------------------------------- contact
CONTACT = '''
<section style="background:linear-gradient(170deg,var(--teal-50),#fff);padding-bottom:36px">
  <div class="wrap narrow center">
    <p class="eyebrow">Contact</p>
    <h1>Talk to a person</h1>
    <p class="lede" style="margin-inline:auto">Commercial quote, custom job, or just a question.
    We reply within one business day &mdash; usually much sooner.</p>
  </div>
</section>

<section style="padding-top:36px">
  <div class="wrap">
    <div class="grid grid-2" style="gap:48px;align-items:start">
      <div>
        <h2>Send us a message</h2>
        <form id="contactForm" novalidate>
          <div id="contactMsg"></div>
          <div class="field-row">
            <div class="field"><label for="cf-name">Your name *</label>
              <input id="cf-name" name="name" type="text" autocomplete="name" required></div>
            <div class="field"><label for="cf-phone">Phone</label>
              <input id="cf-phone" name="phone" type="tel" autocomplete="tel"></div>
          </div>
          <div class="field"><label for="cf-email">Email *</label>
            <input id="cf-email" name="email" type="email" autocomplete="email" required></div>
          <div class="field"><label for="cf-kind">What's this about?</label>
            <select id="cf-kind" name="kind">
              <option value="contact">General question</option>
              <option value="quote">Custom or large-home quote</option>
              <option value="commercial">Office / medical janitorial</option>
              <option value="str">Vacation rental turnovers</option>
              <option value="construction">Post-construction cleaning</option>
              <option value="careers">Joining the team</option>
            </select></div>
          <div class="field"><label for="cf-msg">Message *</label>
            <textarea id="cf-msg" name="message" required
              placeholder="Square footage, how often, anything we should know..."></textarea></div>
          <button class="btn btn-primary btn-lg" type="submit" id="cfBtn">Send message</button>
          <p class="hint">We never share your details, and we don't add you to a mailing list.</p>
        </form>
      </div>
      <aside>
        <div class="card" style="background:var(--sand);border:0">
          <h3>Direct</h3>
          <div id="contactDetails"></div>
        </div>
        <div class="card" style="margin-top:20px">
          <h3>Hours</h3>
          <div id="hoursList"></div>
        </div>
        <div class="card" style="margin-top:20px">
          <h3>Already a client?</h3>
          <p style="font-size:.94rem">Look up, reschedule or cancel a booking without calling.</p>
          <a class="btn btn-ghost btn-sm" href="/track">Track my booking</a>
        </div>
      </aside>
    </div>
  </div>
</section>

<section class="tint-teal">
  <div class="wrap narrow center">
    <h2>Service area</h2>
    <div class="chips" id="areaChips" style="justify-content:center;margin-top:20px"></div>
    <p class="muted" style="margin-top:20px" id="areaNote"></p>
  </div>
</section>
'''
page("contact.html", "Contact %s | Tampa, St. Pete, Clearwater &amp; Sarasota" % NAME,
     "Get in touch for a cleaning quote in Tampa, St. Petersburg, Clearwater or Sarasota.",
     CONTACT, scripts='<script src="/js/contact.js"></script>')

# ---------------------------------------------------------------- track
TRACK = '''
<section style="background:linear-gradient(170deg,var(--teal-50),#fff);padding-bottom:30px">
  <div class="wrap narrow center">
    <p class="eyebrow">Your booking</p>
    <h1>Track a booking</h1>
    <p class="lede" style="margin-inline:auto">Enter the reference from your confirmation
    and the email you booked with.</p>
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
     TRACK, scripts='<script src="/js/track.js"></script>')

# ---------------------------------------------------------------- 404
NF = '''
<section style="padding:110px 0;text-align:center">
  <div class="wrap narrow">
    <p class="eyebrow">404</p>
    <h1>That page got cleaned up</h1>
    <p class="lede" style="margin-inline:auto">The link is broken or the page has moved.
    Here's where most people are headed:</p>
    <div class="btn-row" style="justify-content:center;margin-top:28px">
      <a class="btn btn-primary btn-lg" href="/book">Get a quote</a>
      <a class="btn btn-ghost btn-lg" href="/">Home</a>
      <a class="btn btn-ghost btn-lg" href="/services">Services</a>
    </div>
  </div>
</section>
'''
page("404.html", "Page not found | %s" % NAME, "Page not found.", NF)

print("\n  build_site2.py: remaining pages done")
