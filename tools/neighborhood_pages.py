"""Per-neighbourhood pages for greater Tampa: /cleaning/tampa/<area>.

These only earn their place if each one says something true and specific about
that neighbourhood. Housing stock differs a lot across greater Tampa — 1920s
bungalows in Hyde Park, 2000s production homes in Riverview — and that changes
what a clean actually involves. Thin copies of one template are doorway pages
and Google treats them as such, so every entry below carries its own intro,
housing note and typical-home line.
"""
import html
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

E = html.escape

# (slug, display name, typical home tier, intro, housing note, scheduling note)
AREAS = [
    ("south-tampa", "South Tampa", "t3",
     "South Tampa covers Hyde Park, Palma Ceia, Bayshore Beauharnais and the "
     "streets either side of Bayshore Boulevard. It is one of the oldest parts "
     "of the city and the housing shows it.",
     "A lot of South Tampa is 1920s and 1930s bungalow stock, often renovated "
     "but keeping original heart-pine floors, deep baseboards, picture rails "
     "and clawfoot tubs. Those details hold dust and need hand-wiping rather "
     "than a quick pass, which is why older homes here take longer than their "
     "square footage suggests. Newer infill builds sit next door to them, so we "
     "price on what is actually there.",
     "Street parking is tight on the numbered avenues. Tell us where to park "
     "when you book and we will plan the arrival window around it."),

    ("westchase", "Westchase", "t4",
     "Westchase is a planned community in the north-west of the county, built "
     "largely through the 1990s and 2000s, with a high share of dual-income "
     "households who outsource housework.",
     "Homes here are mostly two-storey production builds of 2,000 to 3,200 sq "
     "ft with tile downstairs, carpet upstairs and screened lanais. The "
     "repeated floor plans mean a crew that has cleaned one Westchase home "
     "works efficiently in the next. Lanai sliders and tile grout are the two "
     "things that most often get skipped by other cleaners here.",
     "Several Westchase villages have gated entries. Leave us a gate code when "
     "you book so the crew is not waiting at the callbox."),

    ("carrollwood", "Carrollwood", "t4",
     "Carrollwood and Original Carrollwood sit north of the city around the "
     "lake, with a mix of mature 1960s-80s homes on larger lots and newer "
     "builds closer to Dale Mabry.",
     "Older Carrollwood homes often have terrazzo or original tile, popcorn "
     "ceilings and generous storage, and the mature oak canopy means more "
     "pollen and leaf litter tracked indoors through spring. Homes back onto "
     "the lake tend to need more glass work than average.",
     "Dale Mabry traffic affects morning arrival windows. Our 8:00 AM slot is "
     "the most reliable here."),

    ("brandon", "Brandon", "t3",
     "Brandon sits east of the city off I-75 and the Crosstown, a large "
     "suburban area that has grown steadily since the 1980s.",
     "Housing runs from 1980s ranch homes on quarter-acre lots to newer "
     "subdivisions off Bloomingdale and Lumsden. Single-storey layouts of "
     "1,500 to 2,200 sq ft are the norm, usually tile and carpet, often with a "
     "screened pool enclosure that collects more dust than owners expect.",
     "Brandon carries a small drive-time surcharge, shown in your quote before "
     "you book and never added afterwards."),

    ("riverview", "Riverview", "t3",
     "Riverview, south-east of the city along US-301 and I-75, is one of the "
     "fastest-growing parts of Hillsborough County and much of its housing is "
     "less than fifteen years old.",
     "These are mostly production builds with luxury vinyl plank or tile "
     "throughout, open-plan kitchens and minimal trim detail. Newer homes clean "
     "faster for their size, which is reflected in how long we schedule. "
     "Construction dust from ongoing development nearby is a recurring issue on "
     "newly closed homes.",
     "Riverview carries a small drive-time surcharge, shown in your quote "
     "before you book."),

    ("new-tampa", "New Tampa", "t4",
     "New Tampa runs north along Bruce B Downs through Tampa Palms, Hunter's "
     "Green and Cross Creek, built from the late 1980s onwards around golf and "
     "gated communities.",
     "Larger two-storey homes of 2,500 to 3,500 sq ft dominate, frequently with "
     "high entryway ceilings, second-floor landings and plenty of glass. High "
     "fixtures and stair rails are where most of the dust sits, and they are "
     "the first thing a rushed cleaner skips.",
     "Most New Tampa communities are gated. We need a gate code or guest-list "
     "entry recorded on your booking."),

    ("temple-terrace", "Temple Terrace", "t2",
     "Temple Terrace is its own city north-east of downtown, next to USF, "
     "built around the golf course from the 1920s with substantial later "
     "infill.",
     "The housing mix is unusually wide: original Mediterranean-revival homes "
     "near the river, mid-century ranches, and a large rental population near "
     "the university. We do a lot of move-in and move-out work here around "
     "semester changes, and those jobs are priced flat rather than by tier.",
     "Semester turnover in August and May books out early. Reserve a move-out "
     "clean two to three weeks ahead if you can."),

    ("lutz", "Lutz", "t4",
     "Lutz sits north of the city across the Pasco line, a lower-density area "
     "of larger lots, acreage properties and newer gated subdivisions.",
     "Expect bigger homes, longer driveways and more outdoor living space than "
     "the city average, often with wells and septic rather than city services. "
     "Lanais, pool decks and sunroom glass make up more of the job here than "
     "they do closer in.",
     "Lutz is at the northern edge of our core area. Availability is good "
     "mid-week; weekends fill first."),

    ("apollo-beach", "Apollo Beach", "t3",
     "Apollo Beach is a waterfront community on the south-east shore of Tampa "
     "Bay, built around a canal system with direct Gulf access.",
     "Many homes back onto canals, which means salt air, more glass, and "
     "sliding door tracks that collect grit quickly. Waterfront properties "
     "need exterior-facing glass and lanai work far more often than inland "
     "homes of the same size, and we schedule accordingly.",
     "Apollo Beach carries a small drive-time surcharge, shown in your quote "
     "before you book."),
]


def build(page, cfg, name, origin, page_hero, final_cta, icon, img=None):
    """Called from build_markets.py once the shared helpers are available."""
    import json as _json

    tiers = {t["id"]: t for t in cfg["home_tiers"] if t.get("prices")}
    phone_raw = cfg["phone_raw"]

    for slug_, area, tier_id, intro, housing, sched in AREAS:
        t = tiers.get(tier_id) or list(tiers.values())[1]
        price = "$%d" % round(t["prices"]["biweekly"] / 100.0)
        others = [a for a in AREAS if a[0] != slug_][:5]

        schema = _json.dumps({
            "@context": "https://schema.org",
            "@type": "HouseCleaningService",
            "name": "%s — %s" % (name, area),
            "url": "%s/cleaning/tampa/%s" % (origin, slug_),
            "image": origin + "/icons/icon-512.png",
            "description": "House cleaning in %s, Tampa FL. %s" % (area, intro[:120]),
            "telephone": cfg["phone"],
            "email": cfg["email"],
            "priceRange": "$$",
            "address": {"@type": "PostalAddress", "addressLocality": "Tampa",
                        "addressRegion": "FL", "addressCountry": "US"},
            "areaServed": {"@type": "Place", "name": area},
            "parentOrganization": {"@type": "Organization", "name": name,
                                   "url": origin},
        }, indent=2)

        hero = page_hero(
            "%s, Tampa" % E(area),
            "House cleaning in <em>%s.</em>" % E(area),
            E(intro),
            ctas=['<a class="btn btn-primary btn-lg" href="/book">See your %s price</a>' % E(area),
                  '<a class="btn btn-ghost btn-lg" href="tel:%s" data-biz-href="phone">Call us</a>' % phone_raw])

        body = (
            '<section class="h-sec"><div class="wrap p-faq-grid">'
            '<div class="t-body">'
            '<h2>What cleaning in %s actually involves</h2><p>%s</p>'
            '<h2>Getting in</h2><p>%s</p>'
            '<h2>What it costs</h2>'
            '<p>A typical %s home here is a %s. At our most popular every-two-weeks '
            'plan that is <strong>%s a visit</strong>, flat, shown in full before you '
            'book. Your first visit is priced as a deep clean to bring the home to a '
            'maintainable baseline. <a href="/pricing">See the full price list</a>.</p>'
            '<h2>Nearby areas we clean</h2><p>%s &mdash; and the rest of '
            '<a href="/cleaning/tampa">greater Tampa</a>.</p>'
            '</div>'
            '<aside class="p-side rv"><h2>Book %s</h2>'
            '<p>Flat written price in about a minute. No card, no obligation.</p>'
            '<a class="btn btn-accent" href="/book">Get my price</a>'
            '<a class="btn btn-ghost" href="tel:%s" data-biz-href="phone">%s<span data-biz="phone">%s</span></a>'
            '</aside></div></section>'
        ) % (E(area), E(housing), E(sched), E(area), E(t["name"]), price,
             ", ".join('<a href="/cleaning/tampa/%s">%s</a>' % (s, E(a))
                       for s, a, *_ in others),
             E(area), phone_raw, icon("phone"), E(cfg["phone"]))

        page("cleaning/tampa/%s.html" % slug_,
             "House Cleaning in %s, Tampa FL | %s" % (area, name),
             "Professional house cleaning in %s, Tampa. Flat published pricing from "
             "%s a visit, hand-picked independent pros, free re-clean within 24 hours."
             % (area, price),
             hero + body + final_cta(
                 cfg, "Ready when you are.",
                 "Flat written price in about a minute. No card, no obligation."),
             head='<script type="application/ld+json">%s</script>' % schema)

    return ["/cleaning/tampa/%s" % a[0] for a in AREAS]
