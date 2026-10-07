"""/services/cleaning-and-organizing-tampa.

Thirteen leads on the board asked for organizing, several in the same breath as
cleaning: "a cleaner who can organize", "organizing then biweekly cleaning",
"help unpacking, then a cleaner twice a week". We sell it -- $55/hr -- as an
unlabelled checkbox on step four of the booking wizard, and nothing on the site
is findable by anyone searching for it.

Deliberately framed as organizing *alongside* cleaning rather than professional
home organizing, which is a different trade with different training. Claiming
otherwise would be the same mistake as the insurance wording: true-adjacent and
wrong in the impression it leaves.

Called from build_markets.py.
"""
import json

from home_v2 import E, faq_items, final_cta, money
from inner_v2 import book_btn, call_btn, page_hero

URL_PATH = "/services/cleaning-and-organizing-tampa"


def _rate(cfg):
    return next(a["price"] for a in cfg["addons"] if a["id"] == "organize")


def body_for(cfg, origin):
    rate = _rate(cfg)
    t2 = next(t for t in cfg["home_tiers"] if t["id"] == "t2")
    hourly = money(rate)

    hero = page_hero(
        "Cleaning &amp; organizing",
        "A cleaner who also puts things <em>where they go</em>.",
        "Most cleaning leaves a tidy version of the same mess. This is the hour or "
        "two on top where the pantry, the cupboard or the wardrobe actually gets "
        "sorted out.",
        ctas=[book_btn(cfg, "Get my price"), call_btn(cfg)],
        proof=["%s an hour, only the hours you want" % hourly,
               "Booked alongside a clean", "Nothing thrown away without asking"])

    honest = f'''
<section class="h-sec"><div class="wrap narrow rv">
  <h2>What this is, and what it isn't</h2>
  <p class="lede">It is organizing done by your cleaner, by the hour, while they
  are already in your home. A drawer that never shuts, a pantry you cannot see
  the back of, a wardrobe after a season change.</p>
  <p><strong>It is not professional home organizing.</strong> That is a separate
  trade with its own training, and if you want someone to redesign how your whole
  house is stored, you want a specialist rather than us. We will say so rather
  than take the booking.</p>
  <p>Nothing is thrown away, donated or moved out of a room without asking you
  first. That is the part people are actually nervous about, and it is the part
  we are strictest on.</p>
</div></section>'''

    jobs = [
      ("Kitchen &amp; pantry", "Everything out, surfaces done underneath, like with like "
       "going back. Out-of-date food flagged, not binned without asking."),
      ("Wardrobes &amp; drawers", "Seasonal swaps, folded and hung back properly. We will "
       "make a donate pile; what happens to it is your call."),
      ("After a move", "The boxes nobody has opened. Unpacked, put somewhere sensible, "
       "boxes broken down and stacked."),
      ("Garage, laundry, linen", "The rooms that quietly become storage. Shelved, "
       "grouped, labelled if you want."),
    ]
    what = '''
<section class="h-sec alt"><div class="wrap">
  <div class="rv"><h2>Where the hour usually goes</h2></div>
  <div class="h-grid-4 h-promises">%s</div>
</div></section>''' % "".join(
        f'<div class="rv"><h3>{h}</h3><p>{b}</p></div>' for h, b in jobs)

    two_hours = rate * 2
    pricing = f'''
<section class="h-sec"><div class="wrap narrow rv">
  <h2>What it costs</h2>
  <p class="lede"><strong>{hourly} an hour</strong>, added to a clean, and only for
  the hours you actually ask for. There is no package and no minimum beyond one
  hour.</p>
  <p>Most people start with two hours on top of a normal visit &mdash; that is
  <strong>{money(two_hours)}</strong> on top of the cleaning price, and it is
  usually enough for one room or one serious cupboard. A {E(t2["name"])} home
  cleaned monthly at {money(t2["prices"]["monthly"])} with two hours of organizing
  comes to <strong>{money(t2["prices"]["monthly"] + two_hours)}</strong> for that
  visit.</p>
  <p>We tell you at the end how far we got and what is left, so the next visit is
  your decision rather than an open meter.</p>
</div></section>'''

    faqs = [
      {"q": "Can I book organizing without a clean?",
       "a": "We would rather you didn't. It is priced as an add-on because the person "
            "doing it is already there for the cleaning, which is what keeps it at %s an "
            "hour. A standalone visit would cost more and be worse value." % hourly},
      {"q": "Will you throw things away?",
       "a": "Not without asking. We will make a pile and show you. What happens to it is "
            "entirely your decision, every time."},
      {"q": "Is this the same as a professional organizer?",
       "a": "No. A professional organizer redesigns how your home is stored and is trained "
            "for it. This is practical sorting by the hour, done by your cleaner. If you "
            "want the former we will tell you so."},
      {"q": "How many hours will it take?",
       "a": "A single cupboard or pantry is usually one to two hours. A full wardrobe swap "
            "or a garage is a half day. We will give you an honest estimate before "
            "starting and tell you where we got to."},
      {"q": "Do you bring boxes or labels?",
       "a": "No, and we would rather not sell you any. If you want particular baskets or "
            "labels, buy what suits your home and we will use them."},
    ]
    faq_sec = '''
<section class="h-sec alt"><div class="wrap narrow">
  <div class="rv"><h2>Questions</h2></div>
  <div class="p-faq rv">%s</div>
</div></section>''' % faq_items(faqs)

    cta = final_cta(cfg, "Book the clean, add the hours",
                    "Pick your home size and frequency, then add organizing on the "
                    "extras step. You will see the full price before anything is booked.")

    schema = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Service", "@id": origin + URL_PATH + "#service",
             "name": "Cleaning and Home Organizing",
             "serviceType": "House cleaning with hourly organizing",
             "areaServed": [{"@type": "City", "name": c} for c in cfg["service_area"][:12]],
             "provider": {"@type": "HouseCleaningService", "name": cfg["name"],
                          "url": origin + "/", "telephone": cfg["phone"]},
             "offers": {"@type": "Offer", "priceSpecification": {
                 "@type": "UnitPriceSpecification",
                 "price": "%.2f" % (rate / 100.0),
                 "priceCurrency": cfg["pricing"]["currency"],
                 "unitText": "hour"}}},
            {"@type": "FAQPage", "@id": origin + URL_PATH + "#faq",
             "mainEntity": [{"@type": "Question", "name": f["q"],
                             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                            for f in faqs]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": origin + "/"},
                {"@type": "ListItem", "position": 2, "name": "Services",
                 "item": origin + "/services"},
                {"@type": "ListItem", "position": 3, "name": "Cleaning and organizing",
                 "item": origin + URL_PATH}]},
        ]}, separators=(",", ":"))

    title = "Cleaning &amp; Home Organizing in Tampa | Tampa Maids"
    desc = ("House cleaning with hourly organizing across greater Tampa. %s an hour on "
            "top of a clean, nothing thrown away without asking." % hourly)
    return hero + honest + what + pricing + faq_sec + cta, schema, desc, title


def build_organizing_page(cfg, page, origin):
    body, schema, desc, title = body_for(cfg, origin)
    assert len(desc) <= 160, len(desc)
    assert len(title) - 4 <= 60, len(title)        # &amp; renders as one char
    page("services/cleaning-and-organizing-tampa.html", title, E(desc), body,
         head='<script type="application/ld+json">%s</script>' % schema,
         scripts='<script src="/js/home.js"></script>', photo="hero")
    return [URL_PATH]
