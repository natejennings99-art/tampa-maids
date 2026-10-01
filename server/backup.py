"""Consistent backups of the booking database.

SQLite in WAL mode cannot be safely backed up by copying the file — a plain copy
can catch a half-written transaction and leave recent bookings in the -wal file.
These helpers use SQLite's online backup API, which is safe while the server is
serving requests.
"""
import csv
import io
import json
import os
import sqlite3
import datetime

import db


def snapshot_bytes():
    """A consistent copy of the whole database, as bytes."""
    src = db.connect()
    mem = sqlite3.connect(":memory:")
    try:
        src.backup(mem)                      # online backup API, transaction-safe
        tmp = db.DB_PATH + ".snapshot"
        out = sqlite3.connect(tmp)
        try:
            mem.backup(out)
        finally:
            out.close()
        with open(tmp, "rb") as f:
            data = f.read()
        os.remove(tmp)
        return data
    finally:
        mem.close()
        src.close()


def bookings_csv():
    """Every booking flattened for a spreadsheet — the format an owner can
    actually use, and readable without this application existing."""
    con = db.connect()
    rows = db.rows(con.execute("""
        SELECT b.ref, b.date, b.slot, b.status, b.service_id, b.frequency,
               b.total_cents, b.is_first_clean, b.created_at, b.completed_at,
               b.access_notes, b.notes, b.terms_version, b.terms_accepted_at,
               c.name, c.email, c.phone, c.address, c.city, c.zip,
               s.name AS crew
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        LEFT JOIN staff s ON s.id = b.assigned_to
        ORDER BY b.date DESC, b.slot
    """))
    con.close()

    buf = io.StringIO()
    cols = ["ref", "date", "slot", "status", "service_id", "frequency", "total",
            "is_first_clean", "created_at", "completed_at", "crew",
            "name", "email", "phone", "address", "city", "zip",
            "access_notes", "notes", "terms_version", "terms_accepted_at"]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        r["total"] = "%.2f" % (r.pop("total_cents", 0) / 100.0)
        r["is_first_clean"] = "yes" if r.get("is_first_clean") else "no"
        w.writerow(r)
    return buf.getvalue()


def customers_csv():
    con = db.connect()
    rows = db.rows(con.execute(
        "SELECT name,email,phone,address,city,zip,notes,created_at,"
        "(SELECT COUNT(*) FROM bookings WHERE customer_id=customers.id) AS bookings "
        "FROM customers ORDER BY created_at DESC"))
    con.close()
    buf = io.StringIO()
    cols = ["name", "email", "phone", "address", "city", "zip", "bookings",
            "notes", "created_at"]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def write_local(dirpath=None):
    """Write a timestamped snapshot + CSVs to disk. Use from cron."""
    dirpath = dirpath or os.path.join(db.DATA_DIR, "backups")
    os.makedirs(dirpath, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    paths = {}
    p = os.path.join(dirpath, "bookings-%s.db" % stamp)
    with open(p, "wb") as f:
        f.write(snapshot_bytes())
    paths["db"] = p
    for name, fn in (("bookings", bookings_csv), ("customers", customers_csv)):
        p = os.path.join(dirpath, "%s-%s.csv" % (name, stamp))
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(fn())
        paths[name] = p

    # keep the last 14 snapshots so a 1 GB disk never fills
    keep = 14
    for prefix in ("bookings-", "customers-"):
        files = sorted(x for x in os.listdir(dirpath) if x.startswith(prefix))
        for old in files[:-keep]:
            try:
                os.remove(os.path.join(dirpath, old))
            except OSError:
                pass
    return paths


if __name__ == "__main__":
    db.init()
    for k, v in write_local().items():
        print("  %-10s %s (%d KB)" % (k, v, os.path.getsize(v) // 1024 or 1))
