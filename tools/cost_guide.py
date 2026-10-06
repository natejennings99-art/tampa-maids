"""/house-cleaning-cost-tampa: what a cleaning actually costs in Tampa Bay.

"how much does house cleaning cost in tampa" is high-volume and high-intent, and
most competitors answer it with "call for a quote" because they price by the
hour on the phone. We publish flat rates, so we can simply answer the question
on the page -- which is both the honest thing and the reason this page can rank.

Every number is read from business.json so the guide can never drift from the
price table the booking form charges. Called from build_markets.py.
"""
import json

from home_v2 import E, faq_items, final_cta, money, slug
from inner_v2 import book_btn, call_btn, page_hero, price_matrix

URL_PATH = "/house-cleaning-cost-tampa"


def _svc(cfg, sid):
    return next((s for s in cfg["services"] if s["id"] == sid), None)


def _range(cfg, sid):
    s = _svc(cfg, sid) or {}
    lo, hi = s.get("price_min"), s.get("price_max")
    return "%s to %s" % (money(lo), money(hi)) if lo and hi else None


def cost_guide_body(cfg, origin):
    tiers = [t for t in cfg["home_tiers"] if t.get("prices")]
    t2 = next((t for t in tiers if t["id"] == "t2"), tiers[0])
    t3 = next((t for t in tiers if t["id"] == "t3"), tiers[-1])
    low = min(t["prices"]["biweekly"] for t in tiers)
    high = max(t["prices"]["once"] for t in tiers)
    zones = (cfg.get("surcharge_zones") or {}).get("cities") or {}
    sur_lo, sur_hi = (min(zones.values()), max(zones.values())) if zones else (0, 0)

    hero = page_hero(
        "Tampa Bay cost guide",
        "How much does house cleaning cost in Tampa?",
        "Most cleaning companies will not tell you until someone has walked your home. "
        "Here are our actual prices, the same ones the booking form charges.",
        ctas=[book_btn(cfg, "Get my exact price"), call_btn(cfg)],
        proof=["Flat rates, not hourly", "No card to see a price", "Quoted before we start"])

    # The direct answer, first, in one paragraph. This is the bit that earns a
    # featured snippet, and burying it would waste the page.
    answer = f'''
<section class="h-sec"><div class="wrap narrow rv">
  <h2>The short answer</h2>
  <p class="lede">In the Tampa Bay area a recurring house cleaning typically runs
  <strong>{money(low)} to {money(t3["prices"]["monthly"])} per visit</strong>, depending on
  the size of the home and how often you book. A one-time or first-time deep clean
  costs more, generally <strong>{money(t2["prices"]["once"])} to {money(high)}</strong>,
  because it covers built-up grime a maintenance visit does not reach.</p>
  <p>A {E(t2["name"].lower())} home cleaned every two weeks is
  <strong>{money(t2["prices"]["biweekly"])}</strong>. The same home cleaned monthly is
  <strong>{money(t2["prices"]["monthly"])}</strong>, because more time passes between visits.
  A {E(t3["name"].lower())} every two weeks is <strong>{money(t3["prices"]["biweekly"])}</strong>.</p>
</div></section>'''

    matrix = f'''
<section class="h-sec alt"><div class="wrap">
  <div class="rv"><h2>Every price, by home size and frequency</h2>
  <p class="lede">These are flat per-visit prices. Tap any number to start a booking
  at that rate.</p></div>
  {price_matrix(cfg)}
</div></section>'''

    # One-off work priced as a range rather than a tier.
    jobs = []
    for sid, label, note in (
            ("deep", "Deep clean", "A full reset: baseboards, inside the oven and fridge, vents, grout."),
            ("move", "Move-in / move-out", "Empty property, priced to pass a landlord walkthrough."),
            ("str", "Airbnb turnover", "Same-day turn, linens re-set, photos after every clean."),
            ("construction", "Post-construction", "Multi-pass fine-dust removal after a build or remodel.")):
        s = _svc(cfg, sid)
        if not s:
            continue
        if sid == "deep":
            amount = "%s to %s" % (money(t2["prices"]["once"]), money(high))
        else:
            amount = _range(cfg, sid) or "Quoted per job"
        jobs.append(f'''<div class="rv"><h3>{E(label)}</h3>
          <p class="amt-big">{amount}</p><p>{E(note)}</p></div>''')

    onetime = f'''
<section class="h-sec"><div class="wrap">
  <div class="rv"><h2>One-time jobs</h2>
  <p class="lede">Priced per job rather than per visit, and quoted firm before anyone starts.</p></div>
  <div class="h-grid-3">{"".join(jobs)}</div>
</div></section>'''

    addons = "".join(f'<li><span>{E(a["name"])}</span><strong>{money(a["price"])}</strong></li>'
                     for a in cfg.get("addons", []) if a.get("price"))

    factors = f'''
<section class="h-sec alt"><div class="wrap narrow">
  <div class="rv"><h2>What actually changes the price</h2></div>
  <div class="rv">
    <h3>Size of the home</h3>
    <p>The single biggest factor. Our tiers run by bedrooms and square footage, from
    under 900 sq ft up to 3,000. Above 3,000 sq ft we quote individually rather than
    guess.</p>
    <h3>How often you book</h3>
    <p>Weekly is cheapest per visit because less builds up between cleans. Monthly costs
    more per visit for the same reason. A one-time clean is the dearest per visit of all.</p>
    <h3>Condition, not just size</h3>
    <p>First visits include a deep clean at <strong>+{int(round(cfg["pricing"]["first_clean_premium"] * 100))}%</strong>
    one time, to bring the home to a baseline the recurring price can maintain. After
    that you pay the standard rate.</p>
    <h3>Where you are</h3>
    <p>Tampa, St. Petersburg and Clearwater carry no travel charge. Outlying areas add
    a drive-time charge between <strong>{money(sur_lo)}</strong> and
    <strong>{money(sur_hi)}</strong>, shown before you book rather than added afterwards.</p>
    <h3>Extras you choose</h3>
    <p>Only if you want them:</p>
    <ul class="p-addons">{addons}</ul>
  </div>
</div></section>'''

    hourly = f'''
<section class="h-sec"><div class="wrap narrow rv">
  <h2>Hourly or flat rate?</h2>
  <p>Plenty of Tampa cleaners quote by the hour, usually $25 to $50 an hour per cleaner.
  The trouble with an hourly rate is that you cannot know the bill until the work is
  finished, and a slower clean costs you more rather than less.</p>
  <p>We price per visit instead. You see the number before you book, it does not move
  once quoted, and if something gets missed we come back and redo it rather than
  charging for another hour.</p>
</div></section>'''

    faqs = [
        {"q": "How much is a one-time house cleaning in Tampa?",
         "a": "A one-time clean runs %s to %s depending on home size, because a single "
              "visit has to deal with everything at once rather than maintaining a baseline."
              % (money(t2["prices"]["once"]), money(high))},
        {"q": "Why does the first clean cost more?",
         "a": "The first visit is a deep clean, charged at +%d%% once. It brings the home to a "
              "standard the recurring price can hold. Every visit after that is the standard rate."
              % int(round(cfg["pricing"]["first_clean_premium"] * 100))},
        {"q": "Is it cheaper to book weekly or monthly?",
         "a": "Weekly costs the least per visit and monthly the most, because the longer the gap "
              "between cleans the more there is to do. Monthly still costs less per month overall."},
        {"q": "Do you charge extra to travel to my area?",
         "a": "Tampa, St. Petersburg and Clearwater have no travel charge. Outlying areas add %s "
              "to %s for drive time, and it is shown in your quote before you book, never added after."
              % (money(sur_lo), money(sur_hi))},
        {"q": "Do I have to give a card to see a price?",
         "a": "No. The booking form prices your home with no card and no email address. You only "
              "enter details if you decide to book."},
    ]
    faq_sec = f'''
<section class="h-sec alt"><div class="wrap narrow">
  <div class="rv"><h2>Common questions about cost</h2></div>
  <div class="p-faq rv">{faq_items(faqs)}</div>
</div></section>'''

    cta = final_cta(cfg, "See your price in under a minute",
                    "Pick your home size and how often you want us. The number is flat, "
                    "and nothing is charged to see it.")

    body = hero + answer + matrix + onetime + factors + hourly + faq_sec + cta

    schema = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "FAQPage", "@id": origin + URL_PATH + "#faq",
             "mainEntity": [{"@type": "Question", "name": f["q"],
                             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]},
            {"@type": "BreadcrumbList",
             "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Home", "item": origin + "/"},
                 {"@type": "ListItem", "position": 2, "name": "Pricing", "item": origin + "/pricing"},
                 {"@type": "ListItem", "position": 3, "name": "Tampa cost guide",
                  "item": origin + URL_PATH}]},
        ]}, separators=(",", ":"))

    title = "How Much Does House Cleaning Cost in Tampa? (2026 Prices)"
    desc = ("Real Tampa house cleaning prices: %s to %s per visit recurring, %s to %s for a "
            "one-time deep clean. Flat rates, no card to see a number."
            % (money(low), money(t3["prices"]["monthly"]),
               money(t2["prices"]["once"]), money(high)))
    return body, schema, desc, title


def build_cost_guide(cfg, page, origin):
    body, schema, desc, title = cost_guide_body(cfg, origin)
    assert len(desc) <= 160, len(desc)
    page("house-cleaning-cost-tampa.html", title, E(desc), body,
         head='<script type="application/ld+json">%s</script>' % schema,
         scripts='<script src="/js/home.js"></script>', photo="hero")
    return [URL_PATH]
