"""Homepage body for the 2026-09 redesign, rendered statically from business.json.

Everything a search engine or a slow phone needs is plain HTML here; web/js/home.js
only adds the live price picker, counters, scroll reveals and the mobile booking bar.
Photos are free-licence Unsplash images served from their CDN (commercial use, no
attribution required) until Tampa Maids has its own job photography.
"""
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "server"))
from checklists import RESIDENTIAL  # noqa: E402

E = html.escape

PHOTOS = {
    # Cleaning-in-action set (bright, natural light) chosen 2026-09-30.
    "hero": "photo-1758273705723-26ef454252ce",          # wiping a table, subject right of the quote card
    "residential": "photo-1765970101624-31e3a737d90e",   # two-person team, modern living room
    "deep": "photo-1642505172378-a6f5e5b15580",          # scrubbing a kitchen sink
    "move": "photo-1646980241033-cd7abda2ee88",          # arriving with caddy and broom
    "str": "photo-1763478958716-bf86c217ce64",           # setting up a guest bed
    "commercial": "photo-1627905646269-7f034dcc5738",    # gloved hands cleaning an office desk
    "construction": "photo-1581578949510-fa7315c4c350",
    "products": "photo-1528740561666-dc2479dc08ab",
    "about": "photo-1581578731548-c64695cc6952",         # cleaner at a window
    # market pages
    "tampa": "photo-1561063139-e183e66909c4",
    "st-petersburg": "photo-1650416942198-35d0d4b7ccfa",
    "clearwater": "photo-1653571763003-91ddee7ecd87",
    "sarasota": "photo-1745423276512-8dd4d9b3140f",
}

ICONS = {
    "check": '<path d="M5 12.5l4.2 4.2L19 7"/>',
    "shield": '<path d="M12 3l7.5 3v5.6c0 4.6-3.2 8.2-7.5 9.4-4.3-1.2-7.5-4.8-7.5-9.4V6z"/><path d="M8.8 12.2l2.2 2.2 4.4-4.6"/>',
    "leaf": '<path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14"/><path d="M5 19l7-7"/>',
    "camera": '<rect x="3" y="7" width="18" height="13" rx="3"/><path d="M8.5 7l1.6-2.5h3.8L15.5 7"/><circle cx="12" cy="13.5" r="3.4"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "tag": '<path d="M3.5 12.3V4.5a1 1 0 0 1 1-1h7.8l8.2 8.2-8.8 8.8z"/><circle cx="8" cy="8" r="1.4"/>',
    "refresh": '<path d="M20 11a8 8 0 0 0-14.3-4.7L4 8"/><path d="M4 4v4h4"/><path d="M4 13a8 8 0 0 0 14.3 4.7L20 16"/><path d="M20 20v-4h-4"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "home": '<path d="M4 11l8-6.5 8 6.5"/><path d="M6 9.8V20h12V9.8"/>',
    "sparkle": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>',
    "box": '<path d="M3.5 7.5L12 3l8.5 4.5v9L12 21l-8.5-4.5z"/><path d="M3.5 7.5L12 12l8.5-4.5M12 12v9"/>',
    "building": '<rect x="5" y="3.5" width="14" height="17" rx="1.5"/><path d="M9 8h1M14 8h1M9 12h1M14 12h1M10.5 20.5v-3.5h3v3.5"/>',
    "hardhat": '<path d="M3.5 17h17M5 17a7 7 0 0 1 14 0"/><path d="M10 10.5V6h4v4.5"/>',
    "mail": '<rect x="3.5" y="5.5" width="17" height="13" rx="2.5"/><path d="M4.5 7l7.5 6 7.5-6"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12l8-8M16 7l2.5 2.5M14 9l2 2"/>',
    "tool": '<path d="M14.5 5.5a4 4 0 0 0-5 5L4 16l4 4 5.5-5.5a4 4 0 0 0 5-5l-2.5 2.5-2.5-.5-.5-2.5z"/>',
    "user": '<circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
    "users": '<circle cx="9" cy="9" r="3.4"/><path d="M3 19.5a6 6 0 0 1 12 0"/><path d="M15.5 5.8a3.2 3.2 0 0 1 0 6.3M17.5 14.2a6 6 0 0 1 3.5 5.3"/>',
    "phone": '<path d="M5 4h3.5l1.7 4.3-2.2 1.4a11 11 0 0 0 6.3 6.3l1.4-2.2L20 15.5V19a1.5 1.5 0 0 1-1.6 1.5A16.5 16.5 0 0 1 3.5 5.6 1.5 1.5 0 0 1 5 4z"/>',
}


def icon(name):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
            % ICONS.get(name, ICONS["sparkle"]))


def img(photo_id, w, alt, cls="", eager=False, ratio=None, sizes=None):
    """Responsive Unsplash image. Width descriptors + `sizes` let a phone fetch a
    ~400px file instead of the 2x desktop one; `sizes` should match the layout."""
    base = "https://images.unsplash.com/%s?auto=format&fit=crop&q=72" % photo_id

    def url(x):
        return "%s&w=%d%s" % (base, x, "&h=%d" % round(x * ratio) if ratio else "")
    widths = sorted({round(w * f) for f in (0.5, 0.75, 1, 1.5, 2)})
    return ('<img src="%s" srcset="%s" sizes="%s" alt="%s"%s %s decoding="async">'
            % (url(w), ", ".join("%s %dw" % (url(x), x) for x in widths),
               sizes or "(max-width: 760px) 92vw, %dpx" % w, E(alt),
               ' class="%s"' % cls if cls else "",
               'fetchpriority="high"' if eager else 'loading="lazy"'))


def money(cents):
    return "$%d" % round(cents / 100)


def slug(name):
    return "".join(c.lower() if c.isalnum() else "-" for c in name).replace("--", "-").strip("-")


def _tiers(cfg):
    return [t for t in cfg["home_tiers"] if t.get("prices")]


def _defaults(cfg):
    tiers, freqs = _tiers(cfg), cfg["frequencies"]
    return (tiers[1] if len(tiers) > 1 else tiers[0],
            next((f for f in freqs if f.get("default")), freqs[0]))


def lowest_price(cfg):
    return min(min(t["prices"].values()) for t in _tiers(cfg))


SERVICE_PAGES = {
    "residential": "house-cleaning-tampa",
    "deep": "deep-cleaning-tampa",
    "move": "move-out-cleaning-tampa",
    "str": "airbnb-cleaning-tampa",
    "commercial": "office-cleaning-tampa",
    "construction": "post-construction-cleaning-tampa",
}


def service_url(sid):
    """Dedicated greater-Tampa page for a service (tools/service_pages.py)."""
    return "/services/%s" % SERVICE_PAGES[sid] if sid in SERVICE_PAGES else "/services#%s" % sid


def service_from(cfg, s):
    """Short "from" price line for a service, straight from the rate card."""
    if s["id"] == "deep":
        # Deep cleans book at the one-time rate (a recurring plan's first visit adds the same premium).
        return "From %s one-time" % money(min(t["prices"]["once"] for t in _tiers(cfg) if "once" in t["prices"]))
    if s["kind"] == "residential":
        return "From %s / visit" % money(lowest_price(cfg))
    if s.get("price_min"):
        return "%s&ndash;%s flat" % (money(s["price_min"]), money(s["price_max"]))
    return "Custom quote"


TRUST = f'''
<div class="h-trust"><div class="wrap">
  <div>{icon("shield")}Personally vetted pros</div>
  <div>{icon("tag")}One flat price, no hourly meter</div>
  <div>{icon("leaf")}EPA Safer Choice products</div>
  <div>{icon("camera")}Before &amp; after photos every visit</div>
  <div>{icon("pin")}Locally owned in Tampa</div>
</div></div>'''


def svc_cards(cfg, only=None):
    out = []
    for s in cfg["services"]:
        if only and s["id"] not in only:
            continue
        pid = PHOTOS.get(s["id"], PHOTOS["residential"])
        out.append(f'''<a class="rv" href="{service_url(s["id"])}">
      <figure>{img(pid, 520, s["name"], ratio=0.625, sizes="(max-width: 760px) 92vw, (max-width: 1180px) 31vw, 362px")}</figure>
      <div class="body"><h3>{E(s["name"])}</h3><p>{E(s["blurb"])}</p>
      <div class="from">{service_from(cfg, s)}<span aria-hidden="true">&rarr;</span></div></div></a>''')
    return "".join(out)


PLAN_PERKS = {
    "weekly": ["Same cleaner every week", "Home stays guest-ready", "Lowest per-visit rate"],
    "biweekly": ["Same cleaner every visit", "Skip or move a visit free (48 hrs notice)", "The sweet spot for most homes"],
    "monthly": ["Monthly reset", "Same checklist and guarantee", "Cancel anytime with 48 hrs' notice"],
    "once": ["Deep clean to our full checklist", "Great before guests or a move", "No commitment"],
}


def plans_grid(cfg):
    default_tier, default_freq = _defaults(cfg)
    once = default_tier["prices"].get("once")
    out = []
    for f in cfg["frequencies"]:
        pr = default_tier["prices"].get(f["id"])
        if pr is None:
            continue
        pop = f is default_freq
        save = ("Save %d%% vs one-time" % round((1 - pr / once) * 100)) if once and f["id"] != "once" and pr < once else "&nbsp;"
        perks = "".join("<li>%s</li>" % E(x) for x in PLAN_PERKS.get(f["id"], []))
        out.append(f'''<div class="h-plan{' pop' if pop else ''} rv">{'<span class="tag">Most popular</span>' if pop else ''}
      <h3>{E(f["name"])}</h3><p class="blurb">{E(f.get("blurb", ""))}</p>
      <div class="price">{money(pr)}</div><p class="per">per visit &middot; {save}</p>
      <ul>{perks}</ul>
      <a class="btn {'btn-accent' if pop else 'btn-ghost'}" href="/book?tier={default_tier["id"]}&amp;freq={f["id"]}">Choose {E(f["name"].lower())}</a></div>''')
    return "".join(out)


def guarantee_list(cfg, n=5):
    return "".join(f'''<div><i>{icon(g.get("icon", "check"))}</i><div><h3>{E(g["title"])}</h3><p>{E(g["text"])}</p></div></div>'''
                   for g in cfg.get("guarantees", [])[:n])


def promise_section(cfg, cls="h-sec", photo="products"):
    return f'''
<section class="{cls}">
  <div class="wrap h-split">
    <figure class="rv">{img(PHOTOS[photo], 640, "Refillable amber spray bottles of plant-based cleaning products", ratio=0.8, sizes="(max-width: 1060px) 92vw, 560px")}</figure>
    <div class="rv"><p class="h-kicker">Our promise</p>
      <h2 style="font-size:clamp(2rem,4vw,2.9rem)">The difference is who we send.</h2>
      <p class="lede">Most cleaning &ldquo;companies&rdquo; are apps that dispatch whoever accepts the job.
      We hand-pick experienced, high-end independent pros &mdash; and put our guarantees in writing.</p>
      <div class="h-list">{guarantee_list(cfg)}</div></div>
  </div>
</section>'''


def checklist_band():
    groups = {}
    for room, task in RESIDENTIAL:
        groups.setdefault(room, []).append(task)
    order = [("Kitchen", "Kitchen"), ("Bathrooms", "Bathrooms"), ("Bedrooms", "Bedrooms & living"), ("Whole home", "Whole home")]
    rooms = []
    for key, label in order:
        tasks = groups.get(key, [])
        if key == "Bedrooms":
            tasks = tasks + groups.get("Living areas", [])
        rooms.append('<div class="h-room rv"><h3>%s</h3><ul>%s</ul></div>'
                     % (E(label), "".join("<li>%s</li>" % E(t) for t in tasks[:5])))
    return f'''
<section class="h-sec h-dark">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">What's included</p>
      <h2>{len(RESIDENTIAL)} points. Every visit. Ticked off in real time.</h2>
      <p>Your cleaner works a written checklist in our app, room by room, and finishes with photos &mdash;
      so you can see the work even when you're not home.</p></div>
    <div class="h-rooms">{"".join(rooms)}</div>
  </div>
</section>'''


def area_cards(cfg, skip=None):
    return "".join(f'''<a class="h-area rv" href="/cleaning/{slug(m["name"])}">
      <h3>{E(m["name"])}</h3><p>{E(m.get("blurb", ""))}</p>
      <div class="towns">{", ".join(E(a) for a in m["areas"] if a != m["name"])}</div>
      <span class="go">House cleaning in {E(m["name"])} &rarr;</span></a>'''
                   for m in cfg.get("markets", []) if m["name"] != skip)


def faq_items(faqs):
    return "".join('<details class="rv"><summary>%s</summary><p>%s</p></details>' % (E(f["q"]), E(f["a"]))
                   for f in faqs)


def final_cta(cfg, title, text, extra=""):
    phone, phone_raw = cfg["phone"], cfg["phone_raw"]
    return f'''
<section class="h-sec">
  <div class="wrap">
    <div class="h-final rv">
      <h2>{title}</h2>
      <p>{text}</p>
      <div class="h-cta" style="justify-content:center;margin:0">
        <a class="btn btn-accent btn-lg" href="/book">Get my instant price</a>
        <a class="btn btn-white btn-lg" href="tel:{phone_raw}" data-biz-href="phone">Call <span data-biz="phone">{E(phone)}</span></a>
      </div>
    </div>{extra}
  </div>
</section>
<div class="m-bar" id="mbar">
  <a class="btn btn-ghost" href="tel:{phone_raw}" data-biz-href="phone">Call</a>
  <a class="btn btn-primary" href="/book">Get my price</a>
</div>'''


def build_home(cfg):
    tiers = _tiers(cfg)
    freqs = cfg["frequencies"]
    markets = cfg.get("markets", [])
    phone, phone_raw = cfg["phone"], cfg["phone_raw"]
    default_tier, default_freq = _defaults(cfg)

    price_data = json.dumps({
        "tiers": [{"id": t["id"], "name": t["name"], "detail": t["detail"], "prices": t["prices"]} for t in tiers],
        "freqs": [{"id": f["id"], "name": f["name"]} for f in freqs],
        "tier": default_tier["id"], "freq": default_freq["id"],
    }).replace("</", "<\\/")

    short = {"weekly": "Weekly", "biweekly": "2 weeks", "monthly": "Monthly", "once": "One-time"}
    seg = "".join('<button type="button" data-freq="%s" aria-pressed="%s">%s</button>'
                  % (f["id"], "true" if f is default_freq else "false", short.get(f["id"], E(f["name"])))
                  for f in freqs)
    opts = "".join('<option value="%s"%s>%s &mdash; %s</option>'
                   % (t["id"], " selected" if t is default_tier else "", E(t["name"]), E(t["detail"])) for t in tiers)
    p0 = default_tier["prices"][default_freq["id"]]

    # ---------------------------------------------------------------- hero
    hero = f'''
<section class="h-hero">
  <div class="wrap h-hero-grid">
    <div class="rv">
      <span class="h-badge"><i>{icon("check")}</i>Now booking this week across greater Tampa</span>
      <h1>Get your time back.<br><em>We'll handle the rest.</em></h1>
      <p class="lede">Hand-picked pro cleaners, a flat price before you book, and a free
      re-clean within 24 hours if anything's missed.</p>
      <div class="h-cta">
        <a class="btn btn-primary btn-lg" href="/book">Get my instant price</a>
        <a class="btn btn-ghost btn-lg" href="tel:{phone_raw}" data-biz-href="phone">{icon("phone")}<span data-biz="phone">{E(phone)}</span></a>
      </div>
      <div class="h-proof">
        <span>{icon("check")}Flat upfront pricing</span>
        <span>{icon("check")}No contracts on home plans</span>
        <span>{icon("check")}Photo-verified visits</span>
      </div>
    </div>
    <div class="h-visual rv">
      <div class="h-photo">{img(PHOTOS["hero"], 720, "A cleaner in yellow gloves wiping down a table in a bright, modern home", eager=True, ratio=1.25, sizes="(max-width: 1060px) 92vw, 540px")}</div>
      <form class="h-quote" id="quote" action="/book" aria-label="Instant price">
        <h2>What will it cost?</h2>
        <p class="sub">Real prices from our published rate card.</p>
        <div class="seg" role="group" aria-label="How often">{seg}</div>
        <label class="sr-only" for="q-tier">Your home</label>
        <select id="q-tier" name="tier">{opts}</select>
        <div class="h-price" aria-live="polite">
          <div><small id="q-cap">Per visit</small><span class="amt" id="q-amt">{money(p0)}</span></div>
          <div class="save" id="q-save"></div>
        </div>
        <button class="btn btn-accent" type="submit">Book this price</button>
        <p class="hint">No card needed to see your total &middot; takes about a minute</p>
        <script type="application/json" id="priceData">{price_data}</script>
      </form>
    </div>
  </div>
</section>'''

    trust = TRUST

    # ---------------------------------------------------------------- stats (all derived from real config)
    n_points = len(RESIDENTIAL)
    n_areas = len(cfg.get("service_area", []))
    stats = f'''
<section class="h-sec">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">The Tampa Maids standard</p>
      <h2>A higher bar, written down.</h2>
      <p>No vague promises. These are the rules every visit is held to.</p></div>
    <div class="h-stats">
      <div class="h-stat rv"><div class="n" data-count="{n_points}">{n_points}</div><p>point checklist, ticked off in our app on every visit</p></div>
      <div class="h-stat rv"><div class="n" data-count="24" data-suffix=" hr">24 hr</div><p>free re-clean window if anything isn't right</p></div>
      <div class="h-stat rv"><div class="n" data-count="{n_areas}">{n_areas}</div><p>neighborhoods served across {len(markets)} markets</p></div>
      <div class="h-stat rv"><div class="n" data-count="0" data-prefix="$">$0</div><p>hidden fees &mdash; the price you see is the price you pay</p></div>
    </div>
  </div>
</section>'''

    steps = '''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head center rv"><p class="h-kicker">How it works</p>
      <h2>Booked in about a minute.</h2>
      <p>No in-home estimate, no phone tag, no salesperson calling you back.</p></div>
    <div class="h-steps">
      <div class="h-step rv"><div class="num">1</div><h3>Tell us about your home</h3>
        <p>Pick your home size and how often. Add extras like inside the oven or fridge.</p></div>
      <div class="h-step rv"><div class="num">2</div><h3>See your exact price</h3>
        <p>A flat, written total before you book &mdash; not a &ldquo;starting at&rdquo; and not an hourly meter.</p></div>
      <div class="h-step rv"><div class="num">3</div><h3>Come home to clean</h3>
        <p>We text when your cleaner is on the way and post before-and-after photos when they finish.</p></div>
    </div>
  </div>
</section>'''

    # ---------------------------------------------------------------- services
    services = f'''
<section class="h-sec" id="services">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Services</p>
      <h2>Every kind of clean, one accountable team.</h2>
      <p>From a biweekly tidy to a nightly medical suite &mdash; same people, same standards, same guarantee.</p></div>
    <div class="h-svc">{svc_cards(cfg)}</div>
  </div>
</section>'''

    # ---------------------------------------------------------------- memberships
    first_note = cfg.get("booking", {}).get("first_clean_note", "")
    memberships = f'''
<section class="h-sec sand" id="plans">
  <div class="wrap">
    <div class="h-head center rv"><p class="h-kicker">Cleaning plans</p>
      <h2>Clean on a schedule. Pay less per visit.</h2>
      <p>Prices shown for a {E(default_tier["name"])} home ({E(default_tier["detail"])}). No contracts &mdash;
      reschedule, pause or cancel with 48 hours' notice.</p></div>
    <div class="h-plans">{plans_grid(cfg)}</div>
    <p class="h-note">{E(first_note)} <a href="/pricing">See every home size &rarr;</a></p>
  </div>
</section>'''

    promise = promise_section(cfg)
    checklist = checklist_band()

    # ---------------------------------------------------------------- reviews: only real, verified ones
    real = [t for t in cfg.get("testimonials", []) if t.get("verified")]
    # With no verified reviews this section used to render as nothing at all,
    # which wastes the one slot where a visitor is actively looking for proof.
    # Every competitor in the local pack shows hundreds of reviews. Pretending
    # otherwise is not an option, so say the true thing instead: we are new,
    # and here is what is written down in place of a reputation.
    reviews = ""
    if not real:
        io = (cfg.get("pricing") or {}).get("intro_offer") or {}
        offer_line = (
            '<p class="h-note" style="text-align:left">Founding clients get '
            '<strong>%s</strong>. That is the trade: you take a chance on a new '
            'company, and it costs you less than the one everybody already '
            'knows.</p>' % E(io["label"])) if io.get("label") else ""
        promises = [
            ("tag", "The price is written down first",
             "You see the full flat price before you book, and it does not move "
             "unless you ask for more work. Nothing is quoted at the door."),
            ("check", "The scope is written down too",
             "The same checklist every visit, so &ldquo;clean&rdquo; is not a matter "
             "of opinion, and you can see exactly what was covered."),
            ("camera", "You get photographs, not assurances",
             "Before and after photos on every visit, uploaded to your record. "
             "You can check the work without being home."),
            ("shield", "If it is wrong, we come back",
             "Tell us within 24 hours and we re-clean the problem free. No "
             "argument about whether it counts."),
        ]
        cards = "".join(
            f'<div class="rv"><i>{icon(i)}</i><h3>{t}</h3><p>{b}</p></div>'
            for i, t, b in promises)
        reviews = f'''
<section class="h-sec sand"><div class="wrap">
  <div class="h-head center rv"><p class="h-kicker">No reviews yet</p>
    <h2>We are new. Here is what we put in writing instead.</h2>
    <p>Every established cleaner in Tampa has hundreds of reviews and we have
    none, because we have not earned them yet. So rather than ask you to take
    our word for anything, these are the things we commit to in advance.</p></div>
  <div class="h-grid-4 h-promises">{cards}</div>
  {offer_line}
</div></section>'''
    if real:
        tiles = "".join(f'''<figure class="quote-tile rv" style="margin:0">
        <p>&ldquo;{E(t["text"])}&rdquo;</p><figcaption class="quote-who">{E(t["name"])}<span>{E(t.get("location", ""))}</span></figcaption></figure>'''
                        for t in real[:6])
        reviews = f'''
<section class="h-sec sand"><div class="wrap">
  <div class="h-head center rv"><p class="h-kicker">Reviews</p><h2>What Tampa Bay says.</h2></div>
  <div class="grid grid-3">{tiles}</div></div></section>'''

    areas = f'''
<section class="h-sec" id="areas">
  <div class="wrap">
    <div class="h-head rv"><p class="h-kicker">Service areas</p>
      <h2>Local to greater Tampa Bay.</h2>
      <p>{E(cfg.get("service_area_note", ""))}</p></div>
    <div class="h-areas">{area_cards(cfg)}</div>
  </div>
</section>'''

    # ---------------------------------------------------------------- faq
    qa = faq_items(cfg.get("faq", [])[:6])
    faq = f'''
<section class="h-sec sand">
  <div class="wrap">
    <div class="h-head center rv"><p class="h-kicker">Questions</p><h2>Good to know.</h2></div>
    <div class="h-faq">{qa}</div>
    <p class="h-note"><a href="/faq">All frequently asked questions &rarr;</a></p>
  </div>
</section>'''

    final = final_cta(cfg, "Your first clean could be this week.",
                      "Get a flat, written price in about a minute. No card required, no obligation.")

    return hero + trust + stats + steps + services + memberships + promise + checklist + reviews + areas + faq + final
