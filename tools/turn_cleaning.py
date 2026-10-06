"""/services/apartment-turn-cleaning-tampa: unit turns for property managers.

The move-out page is written for a resident chasing a deposit back. A property
manager running forty units has a different problem entirely -- every vacant day
costs rent, and a turn that slips by three days costs more than the clean does.
Nothing on the site spoke to them, and a live multifamily enquiry on the lead
board says the demand is real.

Prices come from business.json's one-time tier rates, which is what an empty
unit actually is. Called from build_markets.py.
"""
import json

from home_v2 import E, faq_items, final_cta, money
from inner_v2 import book_btn, call_btn, page_hero

URL_PATH = "/services/apartment-turn-cleaning-tampa"


def _tier(cfg, tid):
    return next(t for t in cfg["home_tiers"] if t["id"] == tid)


def turn_page_body(cfg, origin):
    t1, t2, t3 = _tier(cfg, "t1"), _tier(cfg, "t2"), _tier(cfg, "t3")
    p1, p2, p3 = (money(t["prices"]["once"]) for t in (t1, t2, t3))

    hero = page_hero(
        "Property managers &amp; multifamily",
        "Apartment turn cleaning in Tampa.",
        "Make-ready cleaning priced per unit, scheduled around your move-outs, and "
        "finished to the same checklist every time so you are not inspecting our work.",
        ctas=[book_btn(cfg, "Get per-unit pricing", "/contact"), call_btn(cfg)],
        proof=["Flat price per unit", "Same checklist every turn",
               "Photos of every unit before we leave"])

    # Lead with the PM's actual economics, not ours.
    vacancy = f'''
<section class="h-sec"><div class="wrap narrow rv">
  <h2>A slow turn costs more than the clean</h2>
  <p class="lede">A unit that sits three extra days waiting on a cleaner costs you
  three days of rent. On a $1,800 unit that is about $180 &mdash; roughly what the
  clean itself costs. The cleaning is rarely the expensive part; the delay is.</p>
  <p>So the things we hold ourselves to are the ones that actually move your
  numbers: a turn booked when you tell us the unit is empty, not a week later;
  the same checklist on every unit so the next one is not a surprise; and photos
  sent when we leave, so you can release a unit without driving over to look at it.</p>
</div></section>'''

    pricing = f'''
<section class="h-sec alt"><div class="wrap narrow">
  <div class="rv"><h2>Per-unit pricing</h2>
  <p class="lede">An empty unit is a one-time clean, so it is priced by size rather
  than by the hour. These are the standard rates:</p></div>
  <div class="p-table-wrap rv"><table class="p-table">
    <thead><tr><th>Unit</th><th>Per turn</th></tr></thead>
    <tbody>
      <tr><td><strong>Studio / 1 bed</strong><span>{E(t1["detail"])}</span></td><td class="amt">{p1}</td></tr>
      <tr><td><strong>2 bed</strong><span>{E(t2["detail"])}</span></td><td class="amt">{p2}</td></tr>
      <tr><td><strong>3 bed</strong><span>{E(t3["detail"])}</span></td><td class="amt">{p3}</td></tr>
    </tbody></table></div>
  <p class="h-note rv" style="text-align:left">For a community turning units
  regularly we agree a fixed per-unit schedule up front, so your cost per turn is
  a number you can budget rather than a quote you wait for each time.</p>
</div></section>'''

    scope_items = [
      ("Kitchen", "Inside and outside every cabinet and drawer, inside the oven, "
                  "fridge and freezer, range hood and filter, sink and taps descaled."),
      ("Bathrooms", "Tub, shower, grout and glass descaled, toilet in and behind, "
                    "vanity inside and out, mirrors, extractor vents."),
      ("Throughout", "Walls spot-cleaned, switch plates, door frames and doors, "
                     "skirting, window sills and tracks, blinds, light fittings, vents."),
      ("Floors", "Vacuumed and mopped last, after the dust from everything above "
                 "has settled, so they are clean when the next resident walks in."),
      ("Finish", "Photos of every room sent the same day, so you can release the "
                 "unit without a second visit."),
    ]
    scope = '''
<section class="h-sec"><div class="wrap">
  <div class="rv"><h2>What a turn covers</h2>
  <p class="lede">The same checklist on every unit. No negotiating scope per turn.</p></div>
  <div class="h-grid-3">%s</div>
</div></section>''' % "".join(
        f'<div class="rv"><h3>{E(h)}</h3><p>{E(b)}</p></div>' for h, b in scope_items)

    faqs = [
      {"q": "How quickly can you turn a unit?",
       "a": "We need one day's notice. Tell us the unit is empty and we will clean it "
            "the next working day; most turns are done in a single visit."},
      {"q": "Do you handle several units in the same week?",
       "a": "Yes. Volume is the point of this service, and a regular schedule is "
            "easier for us to staff than one-off jobs. Tell us your typical units "
            "per month and we will price it as a block."},
      {"q": "What does a turn cost?",
       "a": "%s for a studio or one bed, %s for a two bed and %s for a three bed. "
            "A community turning units regularly gets a fixed per-unit schedule "
            "agreed up front." % (p1, p2, p3)},
      {"q": "Do you clean carpets?",
       "a": "No. Carpet extraction is a separate trade and needs a truck-mounted "
            "machine, so you will want a carpet contractor for that. We will work "
            "around whoever you use and clean after them so the carpets dry clean."},
      {"q": "What if a unit is worse than expected?",
       "a": "We tell you before we start, not after we invoice. If a unit needs more "
            "than a standard turn you get a price for the extra work first, and you "
            "decide."},
    ]
    faq_sec = '''
<section class="h-sec alt"><div class="wrap narrow">
  <div class="rv"><h2>Questions property managers ask</h2></div>
  <div class="p-faq rv">%s</div>
</div></section>''' % faq_items(faqs)

    cta = final_cta(cfg, "Tell us your unit mix",
                    "Send your typical unit sizes and how many turns a month, and "
                    "we will come back with a fixed per-unit schedule.")

    body = hero + vacancy + pricing + scope + faq_sec + cta

    schema = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Service", "@id": origin + URL_PATH + "#service",
             "name": "Apartment Turn Cleaning",
             "serviceType": "Make-ready and unit turn cleaning for multifamily properties",
             "areaServed": [{"@type": "City", "name": c} for c in cfg["service_area"][:12]],
             "provider": {"@type": "HouseCleaningService", "name": cfg["name"],
                          "url": origin + "/", "telephone": cfg["phone"]},
             "offers": {"@type": "Offer", "priceSpecification": {
                 "@type": "PriceSpecification",
                 "minPrice": "%.2f" % (t1["prices"]["once"] / 100.0),
                 "maxPrice": "%.2f" % (t3["prices"]["once"] / 100.0),
                 "priceCurrency": cfg["pricing"]["currency"]}}},
            {"@type": "FAQPage", "@id": origin + URL_PATH + "#faq",
             "mainEntity": [{"@type": "Question", "name": f["q"],
                             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                            for f in faqs]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": origin + "/"},
                {"@type": "ListItem", "position": 2, "name": "Services", "item": origin + "/services"},
                {"@type": "ListItem", "position": 3, "name": "Apartment turn cleaning",
                 "item": origin + URL_PATH}]},
        ]}, separators=(",", ":"))

    title = "Apartment Turn Cleaning Tampa | Make-Ready for Property Managers"
    desc = ("Make-ready and unit turn cleaning for Tampa multifamily properties. Flat "
            "per-unit pricing from %s, next-day turns, photos of every unit." % p1)
    return body, schema, desc, title


def build_turn_page(cfg, page, origin):
    body, schema, desc, title = turn_page_body(cfg, origin)
    assert len(desc) <= 160, len(desc)
    page("services/apartment-turn-cleaning-tampa.html", title, E(desc), body,
         head='<script type="application/ld+json">%s</script>' % schema,
         scripts='<script src="/js/home.js"></script>', photo="move")
    return [URL_PATH]
