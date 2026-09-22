# Tampa Maids Cleaning — website + phone app

**tampamaidscleaning.com**

A complete, working booking system built from the business plan in
`Cleaning_Business_Plan_Tampa_StPete.pdf`: a public marketing website, an
installable phone app, an owner's dashboard, and a crew job app — all sharing
one backend.

**No dependencies.** Python 3 standard library only. No `npm`, no `pip install`,
no virtualenv, no build step.

---

## Run it

```bash
./run.sh
```

Then open:

| What | Where | Who |
|---|---|---|
| Website | http://localhost:8000 | Customers |
| Phone app | http://localhost:8000/app | Customers + crew |
| Owner dashboard | http://localhost:8000/admin | You |

To open it on your actual phone, run `./run.sh --lan` and use the URL it
prints. On the phone, open the `/app` URL and choose **Add to Home Screen** —
it installs with its own icon and works offline.

### Sign-in accounts (created on first run)

| Email | Role | Password |
|---|---|---|
| `owner@tampamaidscleaning.com` | Owner — full dashboard | `cleanup2026` |
| `marisol@tampamaidscleaning.com` | Lead — dashboard + jobs | `cleanup2026` |
| `devon@tampamaidscleaning.com` | Cleaner — phone app only | `cleanup2026` |

**Change these before you go live.** Add real staff from Dashboard → Team.

---

## Make it yours

Almost everything lives in one file: **`business.json`**. Edit it and restart —
the website, the app, the quote engine and the dashboard all update together.

Set these before launch:

- `phone`, `phone_raw` — still a placeholder number
- `name`, `short_name`, `domain`, `url` — set to Tampa Maids Cleaning / tampamaidscleaning.com
- `social` links — currently placeholder URLs
- `pricing` and `home_tiers` — already match Section 5 of your business plan
- `markets` — your four markets and the communities in each; drives the
  service-area pages, the homepage grid and the booking city dropdown
- `surcharge_zones.cities` — per-city drive-time surcharge in cents
  (Sarasota-area addresses are $35, the far Tampa Bay zips $15)
- `testimonials` — **placeholder copy, replace before launch** (see below)

All money in `business.json` is in **cents** (`9500` = `$95.00`).

---

## What's built

**Website** — home, services, pricing, about, FAQ, contact, booking wizard,
booking lookup, 404. Responsive, accessible, SEO metadata, FAQ structured data.

**Local SEO pages** — one landing page per market at `/cleaning/tampa`,
`/cleaning/st-petersburg`, `/cleaning/clearwater` and `/cleaning/sarasota`, each
with its own H1, copy, community list, `HouseCleaningService` schema and
canonical URL. Plus `sitemap.xml` and `robots.txt`. Regenerate with
`python3 tools/build_markets.py` after editing `markets` in `business.json`.
These are the pages to point Google Local Services Ads and Google Business
Profile at — the highest-ROI channel named in your plan.

**Booking wizard** — service → size → frequency → add-ons → live calendar →
details. Prices update live and come from the server, never the browser.

**Phone app (PWA)** — installable, offline-capable, bottom tab bar. Customers
book and track cleanings. Crew see their day, get directions, call the client,
and work the digital checklist. Owners get a link into the dashboard.

**Owner dashboard** — overview with revenue and a 7-day forecast, booking
management (confirm, assign crew, reschedule), blocked days, leads inbox, and
team accounts.

**Quote engine** (`server/pricing.py`) implements your plan exactly:
tier × frequency lookup, +35% first-visit deep-clean premium, the 15% bi-weekly
intro offer, drive-time surcharges, per-square-foot commercial rates, and
Florida's residential-exempt / commercial-taxable sales tax rule.

**Checklists** (`server/checklists.py`) — the 37-point residential, 28-point
vacation-rental, and CDC-aligned medical checklists from your plan, plus
move-out and post-construction. Attached to every booking automatically.

---

## Layout

```
business.json          ← all content, pricing and branding
run.sh                 ← start everything
server/
  app.py               ← HTTP server, routing, REST API
  db.py                ← SQLite schema, sessions, password hashing
  pricing.py           ← the quote engine
  checklists.py        ← job checklists
  seed.py              ← creates accounts and demo data
web/
  index.html …         ← marketing pages
  book.html            ← booking wizard
  app/                 ← the installable phone app
  admin/               ← the owner dashboard
  css/  js/  icons/
tools/
  build_site*.py       ← regenerate page chrome (optional)
  make_icons.py        ← regenerate app icons (optional)
data/bookings.db      ← your data
```

Reset the demo data at any time:

```bash
python3 server/seed.py --demo --reset
```

---

## Going live

See **[DEPLOY.md](DEPLOY.md)** for the full walkthrough: GitHub → Render →
GoDaddy DNS → TLS → email. Short version: keep the domain at GoDaddy, host the
app on Render (~$7–8/month), point GoDaddy's A and CNAME records at it.

Production environment variables:

| Variable | Purpose |
|---|---|
| `PORT` / `HOST` | Bind address. Hosts inject `PORT`; use `HOST=0.0.0.0` in a container. |
| `DATA_DIR` | Where `bookings.db` lives. **Must be a persistent disk** or every deploy wipes your data. |
| `TRUST_PROXY` | `1` behind a reverse proxy, so the login throttle sees real client IPs. |
| `FORCE_HTTPS` | `1` to always mark the session cookie `Secure`. |
| `OWNER_EMAIL` / `OWNER_PASSWORD` | Creates your owner account on first boot instead of the default. |

## Before you go live

This runs on Python's built-in HTTP server, which is right for local use, a
demo, or a low-traffic launch. Before taking real customer payments:

1. **Point tampamaidscleaning.com at this server, behind HTTPS.** Sessions use
   cookies; run it behind nginx, Caddy, or a host like Fly.io/Render with TLS
   terminated in front. The canonical URLs, Open Graph tags and LocalBusiness
   structured data already reference the real domain, so search engines and
   link previews resolve correctly the moment DNS points here.
2. **Change every seeded password**, and remove any accounts you don't use.
3. **Add payments.** There's no card processing — bookings are confirmed and
   invoiced manually, matching the plan's "charged on the day of service" model.
   Stripe Checkout drops into the booking confirmation step.
4. **Replace every testimonial with a real review.** The entries in
   `business.json` under `testimonials` are placeholder copy written to show the
   layout. Publishing invented reviews is deceptive and, in the US, an FTC
   matter. Your plan's target of 50+ Google reviews in 90 days is the right
   source — pull the real ones in and delete the `_TODO_testimonials` key.
5. **Add email/SMS.** Confirmations are shown on screen and stored, but nothing
   is emailed yet. `api_create_booking` in `server/app.py` is where to hook in
   Postmark, SES or Twilio.
6. **Back up `data/bookings.db`.** It holds every customer and booking.
