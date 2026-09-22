"""SQLite storage for Tampa Maids Cleaning.

Stdlib only. The schema is created on first run and is safe to re-run.
"""
import os, sqlite3, json, secrets, hashlib, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DATA_DIR lets a host mount a persistent disk somewhere else (e.g. /var/data on
# Render). Without a persistent disk your database is wiped on every deploy.
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "bookings.db")
# Older builds shipped a brand-named file. Keep the name neutral from here on so a
# rebrand never orphans real customer data, and carry any old file across on boot.
_LEGACY_PATHS = [os.path.join(DATA_DIR, "gulfcoast.db"),
                 os.path.join(ROOT, "data", "gulfcoast.db")]

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    email        TEXT NOT NULL,
    phone        TEXT,
    address      TEXT,
    city         TEXT,
    zip          TEXT,
    notes        TEXT,
    referral_credit_cents INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(lower(email));

CREATE TABLE IF NOT EXISTS staff (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    phone         TEXT,
    role          TEXT NOT NULL CHECK (role IN ('owner','lead','cleaner')),
    pw_hash       TEXT NOT NULL,
    pw_salt       TEXT NOT NULL,
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token       TEXT PRIMARY KEY,
    staff_id    INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL,
    expires_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ref            TEXT NOT NULL UNIQUE,
    customer_id    INTEGER NOT NULL REFERENCES customers(id),
    service_id     TEXT NOT NULL,
    tier_id        TEXT,
    frequency      TEXT NOT NULL DEFAULT 'once',
    sqft           INTEGER,
    addons         TEXT NOT NULL DEFAULT '[]',
    date           TEXT NOT NULL,
    slot           TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'requested',
    is_first_clean INTEGER NOT NULL DEFAULT 1,
    quote          TEXT NOT NULL DEFAULT '{}',
    total_cents    INTEGER NOT NULL DEFAULT 0,
    access_notes   TEXT,
    notes          TEXT,
    assigned_to    INTEGER REFERENCES staff(id),
    created_at     TEXT NOT NULL,
    started_at     TEXT,
    completed_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(date);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_assigned ON bookings(assigned_to);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id  INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    area        TEXT NOT NULL,
    label       TEXT NOT NULL,
    done        INTEGER NOT NULL DEFAULT 0,
    sort        INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_tasks_booking ON tasks(booking_id);

CREATE TABLE IF NOT EXISTS blackouts (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    date    TEXT NOT NULL UNIQUE,
    reason  TEXT
);

CREATE TABLE IF NOT EXISTS leads (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    email      TEXT,
    phone      TEXT,
    kind       TEXT NOT NULL DEFAULT 'contact',
    message    TEXT,
    payload    TEXT NOT NULL DEFAULT '{}',
    handled    INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE CASCADE,
    actor      TEXT,
    event      TEXT NOT NULL,
    detail     TEXT,
    created_at TEXT NOT NULL
);
"""


def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat(sep=" ")


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    return con


def _migrate_legacy():
    """Rename a pre-rebrand database into place, WAL sidecars included."""
    if os.path.exists(DB_PATH):
        return
    for old in _LEGACY_PATHS:
        if os.path.exists(old):
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            for suffix in ("", "-wal", "-shm"):
                if os.path.exists(old + suffix):
                    os.rename(old + suffix, DB_PATH + suffix)
            print("  migrated %s -> %s" % (os.path.basename(old), os.path.basename(DB_PATH)))
            return


def init():
    _migrate_legacy()
    con = connect()
    con.executescript(SCHEMA)
    con.commit()
    con.close()


# ---------- passwords ----------

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return h.hex(), salt


def verify_password(password, pw_hash, salt):
    calc, _ = hash_password(password, salt)
    return secrets.compare_digest(calc, pw_hash)


# ---------- helpers ----------

def rows(cur):
    return [dict(r) for r in cur.fetchall()]


def one(cur):
    r = cur.fetchone()
    return dict(r) if r else None


def new_ref(prefix="TM"):
    """Human-friendly booking reference, e.g. TM-7K4Q2M.

    The alphabet omits I, O, 0 and 1 so references survive being read aloud
    over the phone. The prefix comes from business.json.
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "%s-%s" % (prefix, "".join(secrets.choice(alphabet) for _ in range(6)))
