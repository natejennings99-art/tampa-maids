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
# (market slug, area slug, display name, price tier, intro, housing note, access/scheduling note)
AREAS = [
    # ---------------- greater Tampa ----------------
    ("tampa", "south-tampa", "South Tampa", "t3",
     "South Tampa covers Hyde Park, Palma Ceia and the streets either side of Bayshore "
     "Boulevard. It is one of the oldest parts of the city and the housing shows it.",
     "A lot of South Tampa is 1920s and 1930s bungalow stock, often renovated but keeping "
     "original heart-pine floors, deep baseboards and clawfoot tubs. Those details hold dust "
     "and need hand-wiping rather than a quick pass, which is why older homes here take "
     "longer than their square footage suggests.",
     "Street parking is tight on the numbered avenues. Tell us where to park when you book."),
    ("tampa", "westchase", "Westchase", "t4",
     "Westchase is a planned community in the north-west of the county, built largely through "
     "the 1990s and 2000s, with a high share of dual-income households.",
     "Mostly two-storey production builds of 2,000 to 3,200 sq ft with tile downstairs, carpet "
     "upstairs and screened lanais. Lanai sliders and tile grout are the two things most often "
     "skipped by other cleaners here.",
     "Several Westchase villages have gated entries. Leave a gate code when you book."),
    ("tampa", "carrollwood", "Carrollwood", "t4",
     "Carrollwood and Original Carrollwood sit north of the city around the lake, mixing "
     "mature 1960s-80s homes on larger lots with newer builds closer to Dale Mabry.",
     "Older Carrollwood homes often have terrazzo or original tile and popcorn ceilings, and "
     "the mature oak canopy means more pollen and leaf litter tracked indoors through spring.",
     "Dale Mabry traffic affects morning windows. Our 8:00 AM slot is the most reliable here."),
    ("tampa", "brandon", "Brandon", "t3",
     "Brandon sits east of the city off I-75 and the Crosstown, a large suburban area that has "
     "grown steadily since the 1980s.",
     "Housing runs from 1980s ranch homes on quarter-acre lots to newer subdivisions off "
     "Bloomingdale and Lumsden. Single-storey layouts of 1,500 to 2,200 sq ft are the norm, "
     "often with a screened pool enclosure that collects more dust than owners expect.",
     "Brandon carries a small drive-time surcharge, shown in your quote before you book."),
    ("tampa", "riverview", "Riverview", "t3",
     "Riverview, south-east of the city along US-301, is one of the fastest-growing parts of "
     "Hillsborough County and much of its housing is less than fifteen years old.",
     "Mostly production builds with luxury vinyl plank or tile throughout and minimal trim "
     "detail. Newer homes clean faster for their size. Construction dust from nearby "
     "development is a recurring issue on newly closed homes.",
     "Riverview carries a small drive-time surcharge, shown in your quote before you book."),
    ("tampa", "new-tampa", "New Tampa", "t4",
     "New Tampa runs north along Bruce B Downs through Tampa Palms, Hunter's Green and Cross "
     "Creek, built from the late 1980s around golf and gated communities.",
     "Larger two-storey homes of 2,500 to 3,500 sq ft, frequently with high entryway ceilings, "
     "second-floor landings and plenty of glass. High fixtures and stair rails are where the "
     "dust sits and the first thing a rushed cleaner skips.",
     "Most New Tampa communities are gated. We need a gate code or guest-list entry."),
    ("tampa", "temple-terrace", "Temple Terrace", "t2",
     "Temple Terrace is its own city north-east of downtown, next to USF, built around the "
     "golf course from the 1920s with substantial later infill.",
     "An unusually wide mix: original Mediterranean-revival homes near the river, mid-century "
     "ranches, and a large rental population near the university. We do a lot of move-in and "
     "move-out work here around semester changes, priced flat rather than by tier.",
     "Semester turnover in August and May books out early. Reserve two to three weeks ahead."),
    ("tampa", "lutz", "Lutz", "t4",
     "Lutz sits north of the city across the Pasco line, a lower-density area of larger lots, "
     "acreage properties and newer gated subdivisions.",
     "Bigger homes, longer driveways and more outdoor living space than the city average, "
     "often on wells and septic. Lanais, pool decks and sunroom glass make up more of the job "
     "here than they do closer in.",
     "Lutz is at the northern edge of our core area. Mid-week availability is best."),
    ("tampa", "apollo-beach", "Apollo Beach", "t3",
     "Apollo Beach is a waterfront community on the south-east shore of Tampa Bay, built "
     "around a canal system with direct Gulf access.",
     "Many homes back onto canals, which means salt air, more glass, and sliding door tracks "
     "that collect grit quickly. Waterfront properties need exterior-facing glass and lanai "
     "work far more often than inland homes of the same size.",
     "Apollo Beach carries a small drive-time surcharge, shown in your quote before you book."),

    # ---------------- St. Petersburg ----------------
    ("st-petersburg", "downtown-st-pete", "Downtown St. Pete", "t2",
     "Downtown St. Petersburg runs from Beach Drive and the waterfront parks back through the "
     "Edge and Grand Central districts, and it is overwhelmingly condo living.",
     "Most homes here are 800 to 1,400 sq ft condos and lofts in mid- and high-rise buildings, "
     "with hard floors, floor-to-ceiling glass and compact kitchens. Glass and balcony track "
     "work matters more than floor area, and the job is usually quicker than a house of the "
     "same square footage.",
     "Many buildings require a certificate of insurance on file and a loading-dock or service-"
     "elevator booking. Tell us your building at booking and we will handle the paperwork."),
    ("st-petersburg", "snell-isle", "Snell Isle", "t4",
     "Snell Isle is the waterfront enclave north-east of downtown St. Pete, laid out in the "
     "1920s around Coffee Pot Bayou and still one of the most expensive addresses in Pinellas.",
     "Large Mediterranean-revival and modern waterfront homes, frequently 3,000 sq ft and up, "
     "with extensive tile, stone, high ceilings and a lot of glass facing the water. Salt air "
     "means glass and fixtures need attention far more often than inland.",
     "Larger homes here need a longer window than a condo, so we book them early. Weekday mornings "
     "have the most availability."),
    ("st-petersburg", "gulfport", "Gulfport", "t2",
     "Gulfport is the small waterfront arts town on Boca Ciega Bay, south-west of downtown "
     "St. Pete, with a distinctly independent character.",
     "Housing is mostly 1920s-1950s cottages and bungalows on compact lots, many under 1,200 "
     "sq ft, with original wood floors and older tiled bathrooms. Small homes, but the age of "
     "the finishes means detail work rather than speed.",
     "Streets are narrow near the waterfront. Driveway or street parking details help."),
    ("st-petersburg", "pinellas-park", "Pinellas Park", "t2",
     "Pinellas Park sits in the middle of the county between St. Pete and Largo, a practical, "
     "well-established residential city.",
     "Mid-century single-storey homes of 1,000 to 1,700 sq ft dominate, mostly terrazzo or "
     "tile with later laminate, plus a number of 55+ and manufactured-home communities. "
     "Straightforward layouts that clean efficiently.",
     "Good mid-week availability and short drive times from our other Pinellas routes."),
    ("st-petersburg", "st-pete-beach", "St. Pete Beach", "t3",
     "St. Pete Beach is the barrier-island strip from Pass-a-Grille up to Don CeSar, and a "
     "large share of its housing is short-term rental rather than full-time residence.",
     "Beach condos and rental homes with tile throughout, sliding doors onto the Gulf, and "
     "sand in every track and entryway. Turnover cleaning here is its own discipline: linens, "
     "consumables and photo verification inside a check-out to check-in window.",
     "Island addresses carry a small drive-time surcharge. Same-day turn slots are limited in "
     "peak season, so standing bookings get priority."),
    ("st-petersburg", "treasure-island", "Treasure Island", "t3",
     "Treasure Island sits just north of St. Pete Beach on the same barrier island chain, with "
     "a similar mix of vacation rentals, condos and full-time waterfront homes.",
     "Mostly condos and low-rise rental properties facing the Gulf or the intracoastal. Salt "
     "air, sand and sliding-door tracks define the work, and rental units need a reset to a "
     "par list rather than a standard clean.",
     "Treasure Island carries a small drive-time surcharge, shown before you book."),

    # ---------------- Clearwater ----------------
    ("clearwater", "clearwater-beach", "Clearwater Beach", "t3",
     "Clearwater Beach is one of the busiest resort markets in Florida, and most of its "
     "residential stock is condo and vacation rental rather than owner-occupied housing.",
     "High-rise and mid-rise condos with tile floors, balcony sliders and Gulf-facing glass. "
     "Sand and salt are the constant, and rental turnovers run to a fixed checklist with "
     "linens, restocking and photo verification rather than a general clean.",
     "Most beach buildings need a certificate of insurance and a service-elevator slot. Beach "
     "addresses carry a small drive-time surcharge."),
    ("clearwater", "largo", "Largo", "t2",
     "Largo sits in the centre of Pinellas between Clearwater and St. Pete, one of the "
     "county's larger and more affordable residential cities.",
     "Predominantly 1960s-1980s single-storey homes of 1,100 to 1,700 sq ft, plus a "
     "substantial number of 55+ communities and villas. Compact, efficient layouts, often "
     "with original tile and terrazzo under later flooring.",
     "Short drive times from our Clearwater and St. Pete routes mean good availability."),
    ("clearwater", "seminole", "Seminole", "t3",
     "Seminole sits between Largo and the Gulf beaches, a settled suburban city popular with "
     "families and retirees.",
     "Mostly single-family homes of 1,500 to 2,200 sq ft from the 1970s onward, many with "
     "screened pool cages and Florida rooms. Pool cages and lanai glass add work that inland "
     "homes of the same size do not have.",
     "Easy access from Park Boulevard. Mornings fill first with recurring clients."),
    ("clearwater", "dunedin", "Dunedin", "t2",
     "Dunedin is the walkable waterfront town north of Clearwater, known for its historic "
     "downtown, Scottish heritage and the causeway out to Honeymoon Island.",
     "A high proportion of older bungalows and cottages near downtown, many under 1,500 sq ft "
     "with original wood floors and small tiled bathrooms, alongside newer homes and condos "
     "further out. Character homes mean hand-detail work.",
     "Dunedin carries a small drive-time surcharge. Downtown parking is limited at weekends."),
    ("clearwater", "safety-harbor", "Safety Harbor", "t3",
     "Safety Harbor is the small bayfront town on the north-east edge of Pinellas, built "
     "around the spa and the waterfront park.",
     "A mix of older homes near the water and newer subdivisions inland, typically 1,600 to "
     "2,400 sq ft. Mature tree cover means more pollen and leaf debris indoors, especially "
     "spring and after storms.",
     "Good weekday availability. Our Clearwater crews cover Safety Harbor on the same route."),

    # ---------------- Sarasota ----------------
    ("sarasota", "downtown-sarasota", "Downtown Sarasota", "t2",
     "Downtown Sarasota runs from Main Street and the arts district out to the bayfront, and "
     "like downtown St. Pete it is mostly condo living.",
     "Condos and lofts of 900 to 1,500 sq ft with hard floors, large glass and balconies "
     "facing the bay or the city. Glass, balcony tracks and kitchen detail carry the job more "
     "than floor area does.",
     "Most buildings require a certificate of insurance and a booked service elevator. Give us "
     "your building name when you book."),
    ("sarasota", "siesta-key", "Siesta Key", "t3",
     "Siesta Key is the barrier island west of Sarasota with the quartz-sand beach, and a very "
     "high share of its properties are vacation rentals.",
     "Beach condos and rental homes, tile throughout, sliders onto screened lanais, and the "
     "famous fine white sand that gets into every track and entryway. Turnovers here run to a "
     "28-point checklist with linen resets and photo verification.",
     "Siesta Key carries a drive-time surcharge. Peak-season turn windows are tight, so "
     "standing weekly bookings get first call on slots."),
    ("sarasota", "longboat-key", "Longboat Key", "t4",
     "Longboat Key is the long barrier island running north from Sarasota, largely gated, "
     "largely seasonal, and at the top end of the Gulf Coast market.",
     "Large waterfront condos and homes, frequently 2,500 sq ft and up, with stone floors, "
     "extensive glass and high ceilings. A strong snowbird pattern means seasonal open-up and "
     "close-down cleans alongside recurring service.",
     "Gated communities need advance guest-list entry. Longboat Key carries a drive-time "
     "surcharge and seasonal demand peaks November to April."),
    ("sarasota", "lakewood-ranch", "Lakewood Ranch", "t4",
     "Lakewood Ranch, east of Sarasota across into Manatee County, is one of the largest "
     "master-planned communities in the United States and almost entirely new housing.",
     "Production and semi-custom homes of 2,000 to 3,500 sq ft, nearly all built since 2000, "
     "with tile or luxury vinyl plank and open-plan layouts. Newer finishes clean efficiently "
     "for their size, and ongoing construction means post-build dust on recently closed homes.",
     "Lakewood Ranch carries a drive-time surcharge. Most villages are gated, so we need a "
     "gate code or guest-list entry."),
]


MARKET_NAMES = {"tampa": "Tampa", "st-petersburg": "St. Petersburg",
                "clearwater": "Clearwater", "sarasota": "Sarasota"}


def _desc(area, mname, price):
    """Meta description for a neighbourhood page, kept under Google's ~160.

    The old template ran to 172 characters for the longer names, so twelve
    pages were being truncated mid-sentence in the results. It falls back to a
    shorter form rather than letting Google do the cutting, and asserts, because
    a silently truncated description is invisible until someone looks.
    """
    full = ("House cleaning and maid service in %s, %s. Flat prices from %s a visit, "
            "vetted local pros, free re-clean within 24 hours." % (area, mname, price))
    if len(full) <= 160:
        return full
    short = ("House cleaning in %s, %s. Flat prices from %s a visit, free re-clean "
             "within 24 hours." % (area, mname, price))
    assert len(short) <= 160, "description still too long for %s: %d" % (area, len(short))
    return short


def build(page, cfg, name, origin, page_hero, final_cta, icon, img=None):
    """Writes /cleaning/<market>/<area> for every area. Returns the URL paths."""
    import json as _json

    tiers = {t["id"]: t for t in cfg["home_tiers"] if t.get("prices")}
    phone_raw = cfg["phone_raw"]
    urls = []

    for mkt, slug_, area, tier_id, intro, housing, sched in AREAS:
        mname = MARKET_NAMES.get(mkt, mkt.title())
        t = tiers.get(tier_id) or list(tiers.values())[1]
        price = "$%d" % round(t["prices"]["biweekly"] / 100.0)
        # Rotate the "nearby areas" window instead of always taking the first
        # five. A fixed slice gave the earliest areas in each market every
        # internal link and left the rest with only the hub pointing at them --
        # Apollo Beach, Lutz and Temple Terrace had one inbound link each while
        # their neighbours had nine. Starting the window at this page's own
        # position spreads the links evenly and still lists genuine neighbours.
        in_market = [a for a in AREAS if a[0] == mkt]
        here = next((i for i, a in enumerate(in_market) if a[1] == slug_), 0)
        rotated = in_market[here + 1:] + in_market[:here]
        siblings = rotated[:5]

        schema = _json.dumps({
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "HouseCleaningService",
                 "name": "%s — %s" % (name, area),
                 "url": "%s/cleaning/%s/%s" % (origin, mkt, slug_),
                 "image": origin + "/icons/icon-512.png",
                 "description": "Maid service and house cleaning in %s, %s FL." % (area, mname),
                 "telephone": cfg["phone"], "email": cfg["email"], "priceRange": "$$",
                 "address": {"@type": "PostalAddress", "addressLocality": mname,
                             "addressRegion": "FL", "addressCountry": "US"},
                 "areaServed": {"@type": "Place", "name": area},
                 "parentOrganization": {"@type": "Organization", "name": name, "url": origin}},
                {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": origin},
                    {"@type": "ListItem", "position": 2, "name": mname,
                     "item": "%s/cleaning/%s" % (origin, mkt)},
                    {"@type": "ListItem", "position": 3, "name": area,
                     "item": "%s/cleaning/%s/%s" % (origin, mkt, slug_)}]},
            ]}, indent=2)

        hero = page_hero(
            "%s, %s" % (E(area), E(mname)),
            "House cleaning &amp; <em>maid service</em> in %s." % E(area),
            E(intro),
            ctas=['<a class="btn btn-primary btn-lg" href="/book">See your %s price</a>' % E(area),
                  '<a class="btn btn-ghost btn-lg" href="tel:%s" data-biz-href="phone">Call us</a>' % phone_raw])

        body = (
            '<section class="h-sec"><div class="wrap p-faq-grid">'
            '<div class="t-body">'
            '<p class="h-note" style="text-align:left;margin-top:0">'
            '<a href="/">Home</a> &rsaquo; <a href="/cleaning/%s">%s</a> &rsaquo; %s</p>'
            '<h2>What cleaning in %s actually involves</h2><p>%s</p>'
            '<h2>Getting in</h2><p>%s</p>'
            '<h2>What it costs</h2>'
            '<p>A typical %s home here is a %s. At our most popular every-two-weeks plan that '
            'is <strong>%s a visit</strong>, flat, shown in full before you book. Your first '
            'visit is priced as a deep clean to bring the home to a maintainable baseline. '
            '<a href="/pricing">See the full price list</a>.</p>'
            '<h2>Looking for a maid service in %s?</h2>'
            '<p>Maid service, housekeeping, house cleaning &mdash; people call it all three and '
            'mean the same thing: someone reliable who turns up and does a proper job. That is '
            'what we do in %s, weekly, every two weeks or monthly, or as a one-off deep clean. '
            'Same cleaner each visit on a recurring plan.</p>'
            '<h2>Nearby areas we clean</h2><p>%s &mdash; and the rest of '
            '<a href="/cleaning/%s">%s</a>.</p>'
            '</div>'
            '<aside class="p-side rv"><h2>Book %s</h2>'
            '<p>Flat written price in about a minute. No card, no obligation.</p>'
            '<a class="btn btn-accent" href="/book">Get my price</a>'
            '<a class="btn btn-ghost" href="tel:%s" data-biz-href="phone">%s<span data-biz="phone">%s</span></a>'
            '</aside></div></section>'
        ) % (mkt, E(mname), E(area),
             E(area), E(housing), E(sched), E(area), E(t["name"]), price,
             E(area), E(area),
             ", ".join('<a href="/cleaning/%s/%s">%s</a>' % (mkt, s2, E(a2))
                       for _, s2, a2, *_ in siblings) or E(mname),
             mkt, E(mname),
             E(area), phone_raw, icon("phone"), E(cfg["phone"]))

        page("cleaning/%s/%s.html" % (mkt, slug_),
             "Maid Service in %s, %s FL | House Cleaning" % (area, mname),
             _desc(area, mname, price),
             hero + body + final_cta(
                 cfg, "Ready when you are.",
                 "Flat written price in about a minute. No card, no obligation."),
             head='<script type="application/ld+json">%s</script>' % schema)
        urls.append("/cleaning/%s/%s" % (mkt, slug_))

    return urls


# The hub chips come from business.json, which lists the bare city name
# ("St. Petersburg", "Sarasota") where our page is called "Downtown ...".
# Without these aliases those two pages are only reachable from the sitemap.
HUB_ALIASES = {
    "st-petersburg": {"St. Petersburg": "downtown-st-pete"},
    "sarasota": {"Sarasota": "downtown-sarasota"},
}


def areas_for(market_slug):
    """Used by the market hub pages to link their own neighbourhoods."""
    out = {a[2]: a[1] for a in AREAS if a[0] == market_slug}
    out.update(HUB_ALIASES.get(market_slug, {}))
    return out
