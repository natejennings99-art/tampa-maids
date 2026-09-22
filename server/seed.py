#!/usr/bin/env python3
"""Create the owner account and (optionally) demo data.

    python3 server/seed.py                 # accounts only
    python3 server/seed.py --demo          # accounts + sample bookings & leads
    python3 server/seed.py --demo --reset  # wipe and rebuild
"""
import os, sys, json, random, secrets, datetime, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db, pricing, checklists

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "business.json"), encoding="utf-8"))

# Used only for local demo data (--demo). This password is in a public repo, so
# it must never be able to unlock a live install -- see _owner_password().
DEFAULT_PASSWORD = "cleanup2026"

OWNER_EMAIL = os.environ.get("OWNER_EMAIL", "owner@tampamaidscleaning.com")


def _owner_password(demo):
    """Password for the owner account.

    Production (no --demo): use OWNER_PASSWORD if set, otherwise generate a
    random one and print it. We never fall back to DEFAULT_PASSWORD here --
    anyone can read it in the repository, so a forgotten env var would
    otherwise hand over the dashboard.
    """
    env = os.environ.get("OWNER_PASSWORD")
    if env:
        return env, False
    if demo:
        return DEFAULT_PASSWORD, False
    return secrets.token_urlsafe(12), True


def _accounts(demo):
    pw, generated = _owner_password(demo)
    rows = [("Owner", OWNER_EMAIL, "owner", pw, "(813) 555-0142")]
    if demo:
        rows += [
            ("Marisol Vega", "marisol@tampamaidscleaning.com", "lead",    DEFAULT_PASSWORD, "(727) 555-0177"),
            ("Devon Price",  "devon@tampamaidscleaning.com",   "cleaner", DEFAULT_PASSWORD, "(813) 555-0198"),
        ]
    return rows, generated

CUSTOMERS = [
    ("Dana Reyes",     "dana@example.com",   "(727) 555-0110", "412 Brightwaters Blvd NE", "St. Petersburg", "33704"),
    ("Marcus Tolliver","marcus@example.com", "(727) 555-0121", "900 Carillon Pkwy Ste 210", "St. Petersburg", "33716"),
    ("Priya Shah",     "priya@example.com",  "(813) 555-0132", "10412 Countryway Blvd",     "Westchase",      "33626"),
    ("Ellen Whitaker", "ellen@example.com",  "(727) 555-0143", "8820 Park Blvd",            "Seminole",       "33777"),
    ("Andre Mensah",   "andre@example.com",  "(813) 555-0154", "703 S Willow Ave",          "Tampa",          "33606"),
    ("Kelsey Brand",   "kelsey@example.com", "(727) 555-0165", "125 Coral Way",             "Treasure Island","33706"),
    ("Rita Okafor",    "rita@example.com",   "(727) 555-0176", "455 Gulf Blvd Unit 3",      "St. Pete Beach", "33706"),
    ("Tom Vasquez",    "tom@example.com",    "(813) 555-0187", "2201 Providence Lakes",     "Brandon",        "33511"),
]

JOBS = [
    # (customer index, service, tier, frequency, sqft, addons, day offset)
    (0, "residential", "t3", "biweekly", 1900, ["windows"],           -14),
    (0, "residential", "t3", "biweekly", 1900, [],                     0),
    (0, "residential", "t3", "biweekly", 1900, [],                    14),
    (1, "commercial",  None, "weekly",   2200, [],                     1),
    (2, "move",        None, "once",     2400, ["organize"],           3),
    (3, "residential", "t2", "weekly",   1200, ["pets"],               0),
    (3, "residential", "t2", "weekly",   1200, [],                     7),
    (4, "deep",        "t3", "once",     2000, ["blinds", "green"],    2),
    (5, "str",         None, "once",     1100, ["linens"],             0),
    (6, "str",         None, "once",      950, [],                     1),
    (7, "residential", "t4", "monthly",  2600, ["lanai"],              5),
    (2, "residential", "t3", "biweekly", 2100, [],                    -7),
    (4, "residential", "t3", "biweekly", 2000, [],                   -21),
    (5, "str",         None, "once",     1100, [],                    -3),
]

LEADS = [
    ("Sofia Marchetti", "sofia@example.com", "(727) 555-0200", "quote",
     "We manage 6 units on Clearwater Beach and need a turnover partner with a same-day SLA. "
     "Can you quote a monthly rate?"),
    ("Bay Area Dental", "office@example.com", "(813) 555-0211", "commercial",
     "3,100 sq ft dental suite in Westshore, need nightly janitorial starting next month."),
    ("Greg Lindqvist",  "greg@example.com",  "(727) 555-0222", "contact",
     "Do you do post-construction? We finish a kitchen remodel in two weeks."),
]


def run(demo=False, reset=False):
    if reset and os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
        for ext in ("-wal", "-shm"):
            p = db.DB_PATH + ext
            if os.path.exists(p):
                os.remove(p)
        print("  wiped existing database")

    db.init()
    con = db.connect()

    accounts, generated = _accounts(demo)
    made = []
    for name, email, role, pw, phone in accounts:
        if db.one(con.execute("SELECT id FROM staff WHERE lower(email)=lower(?)", (email,))):
            continue
        h, salt = db.hash_password(pw)
        con.execute("INSERT INTO staff (name,email,phone,role,pw_hash,pw_salt,created_at)"
                    " VALUES (?,?,?,?,?,?,?)", (name, email, phone, role, h, salt, db.now()))
        made.append((email, role, pw))
    con.commit()

    if made:
        print("\n  Staff accounts created:")
        for email, role, pw in made:
            print("    %-38s %-8s password: %s" % (email, role, pw))
        if generated:
            print("\n  OWNER_PASSWORD was not set, so a random one was generated")
            print("  and printed above. Save it now -- it is not stored anywhere")
            print("  in readable form and will not be shown again.")
        if any(pw == DEFAULT_PASSWORD for _, _, pw in made):
            print("\n  !! One or more accounts use the default password.")
            print("     Change it before this is reachable from the internet:")
            print("     set OWNER_PASSWORD in your host's environment, or use")
            print("     Dashboard -> Team to add a real account and disable these.")
    else:
        print("  staff accounts already exist — left untouched")

    if not demo:
        con.close()
        return

    if con.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]:
        print("  demo data already present — skipping")
        con.close()
        return

    cust_ids = []
    for name, email, phone, addr, city, zc in CUSTOMERS:
        cur = con.execute(
            "INSERT INTO customers (name,email,phone,address,city,zip,created_at)"
            " VALUES (?,?,?,?,?,?,?)", (name, email, phone, addr, city, zc, db.now()))
        cust_ids.append(cur.lastrowid)

    staff = db.rows(con.execute("SELECT id, role FROM staff"))
    crew = [s["id"] for s in staff if s["role"] in ("lead", "cleaner")]
    slots = CFG["booking"]["time_slots"]
    today = datetime.date.today()
    rng = random.Random(7)
    seen = {}

    for ci, svc, tier, freq, sqft, addons, offset in JOBS:
        d = today + datetime.timedelta(days=offset)
        while d.weekday() == 6:
            d += datetime.timedelta(days=1)
        iso = d.isoformat()
        # respect the 2-jobs-per-slot capacity rule
        slot = next((s for s in slots if seen.get((iso, s), 0) < CFG["booking"]["max_jobs_per_slot"]),
                    slots[0])
        seen[(iso, slot)] = seen.get((iso, slot), 0) + 1

        name, email, phone, addr, city, zc = CUSTOMERS[ci]
        first = offset <= -14
        req = {"service": svc, "tier_id": tier, "frequency": freq, "sqft": sqft,
               "addons": addons, "city": city, "is_first_clean": first,
               "commercial_type": "medical" if svc == "commercial" else None,
               "visits_per_week": 3 if svc == "commercial" else 1}
        q = pricing.quote(CFG, req)
        if q.get("custom_quote") or q.get("error"):
            continue

        if offset < 0:
            status = "completed"
        elif offset == 0:
            status = rng.choice(["confirmed", "in_progress"])
        else:
            status = rng.choice(["requested", "confirmed", "confirmed"])

        ref = db.new_ref(CFG["booking"].get("ref_prefix", "TM"))
        cur = con.execute(
            "INSERT INTO bookings (ref,customer_id,service_id,tier_id,frequency,sqft,addons,"
            "date,slot,status,is_first_clean,quote,total_cents,access_notes,created_at,completed_at,assigned_to)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ref, cust_ids[ci], svc, tier, freq, sqft, json.dumps(addons), iso, slot, status,
             1 if first else 0, json.dumps(q), q["total"],
             rng.choice(["Lockbox code 4417", "Gate code #2210, key under planter",
                         "Door code 8890", "Owner will be home", None]),
             db.now(), db.now() if status == "completed" else None,
             rng.choice(crew) if crew and status != "requested" else None))
        bid = cur.lastrowid

        items = checklists.for_service(svc)
        for i, (area, label) in enumerate(items):
            done = 1 if status == "completed" else (1 if status == "in_progress" and i < len(items) // 3 else 0)
            con.execute("INSERT INTO tasks (booking_id,area,label,done,sort) VALUES (?,?,?,?,?)",
                        (bid, area, label, done, i))
        con.execute("INSERT INTO activity (booking_id,actor,event,detail,created_at)"
                    " VALUES (?,?,?,?,?)", (bid, name, "created", "Seeded demo booking", db.now()))

    for name, email, phone, kind, msg in LEADS:
        con.execute("INSERT INTO leads (name,email,phone,kind,message,payload,created_at)"
                    " VALUES (?,?,?,?,?,?,?)", (name, email, phone, kind, msg, "{}", db.now()))

    # a couple of blackout dates (hurricane-season contingency in the plan)
    for off in (10, 11):
        d = (today + datetime.timedelta(days=off)).isoformat()
        con.execute("INSERT OR REPLACE INTO blackouts (date,reason) VALUES (?,?)",
                    (d, "Team training day"))

    con.commit()
    n = con.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    rev = con.execute("SELECT SUM(total_cents) FROM bookings").fetchone()[0] or 0
    print("  demo data: %d bookings worth %s, %d customers, %d leads"
          % (n, pricing.money(rev), len(cust_ids), len(LEADS)))
    con.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()
    run(demo=a.demo, reset=a.reset)
    print()
