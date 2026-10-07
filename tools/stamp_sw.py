#!/usr/bin/env python3
"""Stamp the service worker's cache version from the shell files it caches.

The worker serves the app shell cache-first, so a phone with the app installed
keeps using its cached /app/app.js until VERSION changes. The file said "bump
this on every shell change" and relied on someone remembering -- which failed
the first time it mattered: the referral field was added to app.js and the
version was left alone, so installed apps would never have shown it.

The version is now a hash of the shell files themselves. Change any of them and
it changes; change none and it does not, so this is safe to run on every build.

    python3 tools/stamp_sw.py          # update if needed
    python3 tools/stamp_sw.py --check  # exit 1 if stale, change nothing
"""
import hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SW = os.path.join(ROOT, "web", "app", "sw.js")
# Only the files whose contents the user would actually see change.
WATCH = ["web/app/index.html", "web/app/app.css", "web/app/app.js",
         "web/js/api.js"]


def shell_hash():
    h = hashlib.sha256()
    for rel in WATCH:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        h.update(rel.encode())
        with open(p, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:12]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    with open(SW, encoding="utf-8") as fh:
        src = fh.read()
    m = re.search(r"const VERSION = '([^']*)';", src)
    if not m:
        sys.exit("No VERSION line in %s" % SW)
    current, want = m.group(1), "tm-" + shell_hash()
    if current == want:
        print("service worker version up to date (%s)" % current)
        return 0
    if check:
        print("STALE: service worker says %s, shell hashes to %s" % (current, want))
        print("Run: python3 tools/stamp_sw.py")
        return 1
    with open(SW, "w", encoding="utf-8") as fh:
        fh.write(src.replace("const VERSION = '%s';" % current,
                             "const VERSION = '%s';" % want))
    print("service worker version %s -> %s" % (current, want))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
