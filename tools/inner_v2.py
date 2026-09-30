"""Inner-page bodies for the 2026-09 redesign: services, pricing, about, FAQ,
contact and the per-market landing pages.

Like the homepage (home_v2.py) these are rendered to plain HTML from
business.json, so prices, checklists and FAQs are in the page source for search
engines and slow phones. web/js/home.js adds the same reveals, counters and
mobile booking bar on every page; web/js/contact.js only handles the form.
"""
from home_v2 import (E, PHOTOS, RESIDENTIAL, TRUST, area_cards, checklist_band, faq_items,
                     final_cta, guarantee_list, icon, img, money, plans_grid, promise_section,
                     service_from, slug, svc_cards, _defaults)


def page_hero(kicker, title, lede, photo=None, alt="", ctas=None, proof=None):
    """Split hero with a photo, or a centred text hero when there is no photo."""
    cta_html = ""
    if ctas:
        cta_html = '<div class="h-cta">%s</div>' % "".join(ctas)
    proof_html = ""
    if proof:
        proof_html = '<div class="h-proof">%s</div>' % "".join(
            "<span>%s%s</span>" % (icon("check"), p) for p in proof)
    text = f'''<div class="rv"><p class="h-kicker">{kicker}</p><h1>{title}</h1>
      <p class="lede">{lede}</p>{cta_html}{proof_html}</div>'''
    if not photo:
        return f'''
<section class="p-hero p-hero-c"><div class="wrap">{text}</div></section>'''
    return f'''
<section class="p-hero">
  <div class="wrap p-hero-grid">
    {text}
    <figure class="p-hero-photo rv">{img(PHOTOS[photo], 640, alt, eager=True, ratio=0.8, sizes="(max-width: 1060px) 92vw, 540px")}</figure>
  </div>
</section>'''


def book_btn(cfg, label="Get my instant price", href="/book"):
    return '<a class="btn btn-primary btn-lg" href="%s">%s</a>' % (href, label)


def call_btn(cfg):
    return ('<a class="btn btn-ghost btn-lg" href="tel:%s" data-biz-href="phone">%s<span data-biz="phone">%s</span></a>'
            % (cfg["phone_raw"], icon("phone"), E(cfg["phone"])))


def rate(r):
    if r.get("per_sqft_min"):
        return "$%.2f&ndash;$%.2f / sq ft" % (r["per_sqft_min"] / 100, r["per_sqft_max"] / 100)
    return "%s&ndash;%s / visit" % (money(r["flat_min"]), money(r["flat_max"]))


def rates_table(rates):
    rows = "".join(f'''<tr><td><strong>{E(r["name"])}</strong><span>{E(r["detail"])}</span></td>
      <td class="amt">{rate(r)}</td><td>{E(r["typical_monthly"])}</td></tr>''' for r in rates)
    return f'''<div class="p-table-wrap rv"><table class="p-table">
      <thead><tr><th>Space</th><th>Rate</th><th>Typical monthly</th></tr></thead>
      <tbody>{rows}</tbody></table></div>'''


def price_matrix(cfg):
    freqs = cfg["frequencies"]
    head = "".join('<th%s>%s%s</th>' % (' class="pop"' if f.get("default") else "", E(f["name"]),
                                        '<small>Most popular</small>' if f.get("default") else "")
                   for f in freqs)
    rows = []
    for t in cfg["home_tiers"]:
        if t.get("custom_quote") or not t.get("prices"):
            cells = '<td colspan="%d" class="custom"><a href="/contact">Custom quote &mdash; tell us about your home &rarr;</a></td>' % len(freqs)
        else:
            cells = "".join('<td class="amt%s"><a href="/book?tier=%s&amp;freq=%s">%s</a></td>'
                            % (" pop" if f.get("default") else "", t["id"], f["id"], money(t["prices"][f["id"]]))
                            for f in freqs)
        rows.append('<tr><td><strong>%s</strong><span>%s</span></td>%s</tr>' % (E(t["name"]), E(t["detail"]), cells))
    return f'''<div class="p-table-wrap rv"><table class="p-table p-matrix">
      <thead><tr><th>Home size</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'''


# ================================================================ services
def services_page(cfg):
    svcs = cfg["services"]
    hero = page_hero(
        "Services", "Every kind of clean.<br><em>One accountable team.</em>",
        "Homes, vacation rentals, offices and job sites across Tampa Bay and Sarasota &mdash; all done by "
        "our own W-2 employees, to a written checklist, with photos when they finish.",
        photo="deep", alt="Scrubbing a kitchen sink during a deep clean",
        ctas=[book_btn(cfg), call_btn(cfg)])

    jump = '<nav class="p-jump" aria-label="Services on this page"><div class="wrap">%s</div></nav>' % "".join(
        '<a href="#%s">%s</a>' % (s["id"], E(s["name"])) for s in svcs)

    arts = []
    for i, s in enumerate(svcs):
        meta = '<p class="p-meta">%s%s</p>' % (icon("clock"), E(s["duration_note"]))
        if s.get("audience"):
            meta += '<p class="p-meta">%s%s</p>' % (icon("users"), E(s["audience"]))
        incl = "".join("<li>%s<span>%s</span></li>" % (icon("check"), E(x)) for x in s["includes"])
        extra = ""
        if s.get("rates"):
            extra = rates_table(s["rates"])
        if s.get("contract_note"):
            extra += '<p class="h-note" style="text-align:left">%s</p>' % E(s["contract_note"])
        second = ('<a class="btn btn-ghost" href="/contact">Request a walkthrough</a>'
                  if s["kind"] == "commercial" or s["id"] == "construction" else "")
        arts.append(f'''
<article class="p-svc{' flip' if i % 2 else ''}" id="{s["id"]}">
  <div class="wrap">
    <div class="p-svc-grid">
      <figure class="rv">{img(PHOTOS.get(s["id"], PHOTOS["residential"]), 620, s["name"], ratio=0.8, sizes="(max-width: 1060px) 92vw, 540px")}</figure>
      <div class="rv">
        <p class="h-kicker">{icon(s.get("icon", "sparkle"))}{"%02d" % (i + 1)}</p>
        <h2>{E(s["name"])}</h2>
        <p class="lede">{E(s["blurb"])}</p>
        {meta}
        <div class="p-price">{service_from(cfg, s)}</div>
        <ul class="p-checks">{incl}</ul>
        <div class="h-cta"><a class="btn btn-primary" href="/book?service={s["id"]}">Get a price</a>{second}</div>
      </div>
    </div>
    {extra}
  </div>
</article>''')

    addons = "".join(f'''<div class="p-addon rv"><h3>{E(a["name"])}</h3>
      <div class="amt">+{money(a["price"])}</div>{'<p>about %d min</p>' % a["minutes"] if a.get("minutes") else '<p>no extra time</p>'}</div>'''
                     for a in cfg["addons"])
    addon_sec = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head center rv"><p class="h-kicker">Add-ons</p>
      <h2>Extras for any visit.</h2>
      <p>Add them when you book, or ask your cleaner on the day &mdash; we re-quote before we start, never after.</p></div>
    <div class="p-addons">{addons}</div>
  </div>
</section>'''
    return (hero + jump + "".join(arts) + addon_sec + checklist_band()
            + final_cta(cfg, "Not sure which one you need?",
                        "Answer four quick questions and we'll show you the right service and an exact price."))


# ================================================================ pricing
def pricing_page(cfg):
    P = cfg["pricing"]
    intro = P.get("intro_offer") or {}
    default_tier, default_freq = _defaults(cfg)
    hero = page_hero(
        "Pricing", "Flat prices.<br><em>Published openly.</em>",
        "No hourly meter, no &ldquo;starting at,&rdquo; no estimate that changes at the door. "
        "This is our full rate card &mdash; the same numbers our booking calculator uses.",
        ctas=[book_btn(cfg, "Calculate my exact price"), call_btn(cfg)],
        proof=["No card needed to see your total", "Reschedule free with 48 hrs' notice",
               "Residential cleaning is sales-tax exempt"])

    offer = ""
    if intro.get("label"):
        req = next((f["name"] for f in cfg["frequencies"] if f["id"] == intro.get("requires")), "")
        offer = f'''<div class="p-offer rv">{icon("tag")}<div><strong>New client offer: {E(intro["label"])}</strong>
          <span>Book the &ldquo;{E(req)}&rdquo; plan online and it&rsquo;s applied automatically.</span></div></div>'''

    recurring = f'''
<section class="h-sec" id="plans">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Recurring house cleaning</p>
      <h2>Priced by home size and how often.</h2>
      <p>Tap any price to book it. {E(default_freq["name"])} is our most popular plan.</p></div>
    {price_matrix(cfg)}
    <p class="h-note" style="text-align:left">{E(cfg["booking"]["first_clean_note"])}</p>
    {offer}
  </div>
</section>
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head center rv"><p class="h-kicker">Compare plans</p>
      <h2>The more often, the less per visit.</h2>
      <p>Shown for a {E(default_tier["name"])} home ({E(default_tier["detail"])}).</p></div>
    <div class="h-plans">{plans_grid(cfg)}</div>
  </div>
</section>'''

    flat = [s["id"] for s in cfg["services"] if s["kind"] == "flat"]
    specialty = f'''
<section class="h-sec">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">One-time &amp; specialty</p>
      <h2>Flat rates, quoted on size and condition.</h2>
      <p>Your exact number is set before we start, in writing.</p></div>
    <div class="h-svc">{svc_cards(cfg, only=flat)}</div>
  </div>
</section>'''

    comm = next((s for s in cfg["services"] if s["kind"] == "commercial"), None)
    commercial = ""
    if comm:
        commercial = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Commercial &amp; janitorial</p>
      <h2>Contracted, predictable, per square foot.</h2>
      <p>For offices, medical and dental suites, and boutique retail. We walk the space first and quote in writing.</p></div>
    {rates_table(comm["rates"])}
    <p class="h-note" style="text-align:left">{E(comm.get("contract_note", ""))} {E(P.get("tax_note", ""))}</p>
    <div class="h-cta"><a class="btn btn-primary" href="/contact">Request a walkthrough</a></div>
  </div>
</section>'''

    words = ("price", "cost", "first clean", "pay", "tax", "cancel")
    pfaq = [f for f in cfg.get("faq", []) if any(w in f["q"].lower() for w in words)]
    faq = f'''
<section class="h-sec">
  <div class="wrap">
    <div class="h-head center rv"><p class="h-kicker">Pricing questions</p><h2>The fine print, in plain English.</h2></div>
    <div class="h-faq">{faq_items(pfaq)}</div>
  </div>
</section>''' if pfaq else ""

    return (hero + recurring + specialty + commercial + promise_section(cfg, "h-sec") + faq
            + final_cta(cfg, "See your exact number.",
                        "The calculator uses the same rate card above. No email or card required to see your price."))


# ================================================================ about
def about_page(cfg):
    n_areas = len(cfg.get("service_area", []))
    hero = page_hero(
        "About us", "Locally owned.<br><em>Personally accountable.</em>", E(cfg["mission"]),
        photo="about", alt="A professional cleaner at work",
        ctas=[book_btn(cfg, "Book your first clean"), call_btn(cfg)])

    glance = [("Founded", cfg["founded"]), ("Based in", "%s, %s" % (cfg["city"], cfg["state"])),
              ("Serving", "%d communities in %d markets" % (n_areas, len(cfg.get("markets", [])))),
              ("Team", "W-2 employees, background-checked"),
              ("Products", "EPA Safer Choice certified"),
              ("Checklist", "%d points, every visit" % len(RESIDENTIAL))]
    glance_html = "".join("<div><span>%s</span><strong>%s</strong></div>" % (E(k), E(v)) for k, v in glance)

    story = f'''
<section class="h-sec">
  <div class="wrap p-story">
    <div class="rv p-prose">
      <p class="h-kicker">Why we started</p>
      <h2>Tampa Bay has plenty of cleaners. Not enough you can count on twice in a row.</h2>
      <p>The national franchises are consistent but rigid and impersonal &mdash; a different pair of
      strangers each visit, and a price set in another state. The gig apps are instant and cheap, but
      there's no vetting, no recourse, and no chance the same person comes back. The small independents,
      many of them excellent, are one bad week away from missing your appointment entirely.</p>
      <p>We built <span data-biz="name">{E(cfg["name"])}</span> in the gap between them: franchise-level
      systems and reliability, at an independent's price, run by someone who lives here and answers the phone.</p>
      <h3>How we're different</h3>
      <p>Everyone who enters your home is our <strong>W-2 employee</strong> &mdash; not a contractor, not a
      gig worker. They're background-checked and E-Verified before their first job, uniformed, paid above
      market with paid drive time, and trained before they ever work unsupervised.</p>
      <p>That costs us more. It's also the whole reason clients stay: the same people show up, they already
      know your home, and if anything goes wrong there's a company standing behind the work.</p>
    </div>
    <aside class="p-glance rv"><h3>At a glance</h3>{glance_html}
      <p class="p-glance-note">{icon("refresh")}If something isn't right, tell us within 24 hours and we re-clean it free.</p>
    </aside>
  </div>
</section>'''

    v_icons = ["shield", "user", "tag", "leaf"]
    values = "".join(f'''<div class="h-step rv"><div class="num">{icon(v_icons[i] if i < len(v_icons) else "check")}</div>
      <h3>{E(v["title"])}</h3><p>{E(v["text"])}</p></div>''' for i, v in enumerate(cfg.get("values", [])))
    values_sec = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head center rv"><p class="h-kicker">What we stand for</p><h2>Four things we don't compromise on.</h2></div>
    <div class="h-steps p-values">{values}</div>
  </div>
</section>'''

    segs = "".join(f'''<div class="p-seg rv"><h3>{E(s["name"])}</h3><p>{E(s["profile"])}</p>
      <dl><div><dt>Typical</dt><dd>{E(s["typical"])}</dd></div><div><dt>How often</dt><dd>{E(s["frequency"])}</dd></div></dl></div>'''
                   for s in cfg.get("segments", []))
    seg_sec = f'''
<section class="h-sec">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Who we serve</p><h2>Homes, rentals and businesses.</h2>
      <p>Different spaces, same standard. Here's what a typical job looks like for each.</p></div>
    <div class="p-segs">{segs}</div>
  </div>
</section>'''

    return (hero + TRUST + story + values_sec + seg_sec + checklist_band()
            + final_cta(cfg, "Meet the team that comes back.",
                        "Book online in about a minute, or call and talk to the owner."))


# ================================================================ faq
def faq_page(cfg):
    hero = page_hero(
        "Questions", "Everything people <em>ask us.</em>",
        'If your question isn\'t here, <a href="tel:%s" data-biz-href="phone">call us</a> or '
        '<a href="/contact">send a message</a> &mdash; a real person replies.' % cfg["phone_raw"])
    body = f'''
<section class="h-sec" style="padding-top:24px">
  <div class="wrap p-faq-grid">
    <div class="h-faq">{faq_items(cfg.get("faq", []))}</div>
    <aside class="p-side rv">
      <h2>Still deciding?</h2>
      <p>Seeing your actual price usually settles it. It takes about a minute and needs no card.</p>
      <a class="btn btn-accent" href="/book">Show me my price</a>
      <a class="btn btn-ghost" href="tel:{cfg["phone_raw"]}" data-biz-href="phone">{icon("phone")}<span data-biz="phone">{E(cfg["phone"])}</span></a>
    </aside>
  </div>
</section>'''
    return hero + body + final_cta(cfg, "Ready when you are.",
                                   "Flat written price in about a minute. No card, no obligation.")


# ================================================================ contact
def contact_page(cfg):
    hero = page_hero(
        "Contact", "Talk to a <em>real person.</em>",
        "Commercial quote, custom job, or just a question. We reply within one business day &mdash; usually much sooner.")
    hours = "".join('<div><strong>%s</strong><span>%s</span></div>' % (k, E(v)) for k, v in [
        ("Residential", cfg["hours"]["residential"]), ("Commercial", cfg["hours"]["commercial"]),
        ("Vacation rentals", cfg["hours"]["vacation_rental"])])
    body = f'''
<section class="h-sec" style="padding-top:24px">
  <div class="wrap p-contact">
    <form id="contactForm" class="p-form rv" novalidate>
      <h2>Send us a message</h2>
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
    <aside class="p-contact-side">
      <div class="p-side rv">
        <h2>Direct</h2>
        <a class="p-line" href="tel:{cfg["phone_raw"]}" data-biz-href="phone">{icon("phone")}<strong data-biz="phone">{E(cfg["phone"])}</strong></a>
        <a class="p-line" href="mailto:{E(cfg["email"])}" data-biz-href="email">{icon("mail")}<span data-biz="email">{E(cfg["email"])}</span></a>
        <p class="p-line">{icon("pin")}<span>{E(cfg["city"])}, {E(cfg["state"])} &middot; {E(cfg["region"])}</span></p>
      </div>
      <div class="p-side rv"><h2>Hours</h2><div class="p-hours">{hours}</div></div>
      <div class="p-side rv">
        <h2>Already a client?</h2>
        <p>Look up, reschedule or cancel a booking without calling.</p>
        <a class="btn btn-ghost" href="/track">Track my booking</a>
      </div>
    </aside>
  </div>
</section>
<section class="h-sec sand" id="areas">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Service area</p><h2>Where we clean.</h2>
      <p>{E(cfg.get("service_area_note", ""))}</p></div>
    <div class="h-areas">{area_cards(cfg)}</div>
  </div>
</section>'''
    return hero + body


# ================================================================ markets
def market_page(cfg, m, angle, surcharged):
    name = m["name"]
    s = slug(name)
    hero = page_hero(
        "%s, Florida" % E(name), "House cleaning in <em>%s.</em>" % E(name), E(angle),
        photo=s if s in PHOTOS else "residential", alt="%s, Florida" % name,
        ctas=[book_btn(cfg, "See my %s price" % E(name)), call_btn(cfg)],
        proof=["This is our home base" if m.get("home_base") else "Dispatched daily from Tampa",
               "Flat upfront pricing", "Photo-verified visits"])

    chips = "".join('<span>%s%s</span>' % (icon("pin"), E(a)) for a in m["areas"])
    sur = ('<p class="h-note" style="text-align:left">A drive-time surcharge applies in %s. '
           'It&rsquo;s shown in your quote before you book, never added afterwards.</p>'
           % ", ".join(E(a) for a in surcharged)) if surcharged else ""
    coverage = f'''
<section class="h-sec">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Coverage</p><h2>Where we clean around {E(name)}.</h2>
      <p>Recurring cleaning, deep cleans, move-outs and more across these communities.</p></div>
    <div class="p-chips rv">{chips}</div>
    {sur}
  </div>
</section>'''

    pricing = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Pricing in {E(name)}</p><h2>Flat rates, published openly.</h2>
      <p>The same rate card everywhere we work. Tap any price to book it.</p></div>
    {price_matrix(cfg)}
    <p class="h-note" style="text-align:left">{E(cfg["booking"]["first_clean_note"])}</p>
  </div>
</section>'''

    services = f'''
<section class="h-sec">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Services</p><h2>What we do in {E(name)}.</h2></div>
    <div class="h-svc">{svc_cards(cfg)}</div>
  </div>
</section>'''

    faq = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head center rv"><p class="h-kicker">Questions</p><h2>Common questions.</h2></div>
    <div class="h-faq">{faq_items(cfg.get("faq", [])[:6])}</div>
  </div>
</section>'''

    others = [x for x in cfg["markets"] if x["name"] != name]
    also = ('<p class="h-note">We also clean in %s.</p>'
            % ", ".join('<a href="/cleaning/%s">%s</a>' % (slug(o["name"]), E(o["name"])) for o in others))
    return (hero + TRUST + coverage + pricing + services + promise_section(cfg) + faq
            + final_cta(cfg, "Book your %s cleaning." % E(name),
                        "Flat written price in about a minute. No card, no obligation, no salesperson calling you back.",
                        extra=also))
