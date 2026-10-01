# Next up — Tampa Maids Cleaning

Resume here. Order matters: 1–6 are legal/insurance exposure, 7–10 are product gaps.
Mirrored in Claude's memory. Updated 2026-09-30.

## Legal & insurance — close these first

1. **Insurance close-out.** Prep for the Insureon agent call: confirm the 1099
   IC exclusion is absent, add care-custody-control and HNOA, settle the bond
   and inland-marine quotes. **Quote expires ~2026-10-30.** The live site
   promises "fully insured before your first clean" — that promise is
   outstanding while bookings are being taken.
2. **Independent Contractor Agreement + onboarding packet.** W-9, per-job pay,
   own equipment, COI naming Tampa Maids as additional insured, hold-harmless,
   key/code confidentiality, non-solicit, FCRA background-check disclosure.
   You told Insureon you'd require these. A Florida attorney should review it.
3. **Client service agreement at booking.** Terms page + "I agree" checkbox on
   /book: scope, 24-hr re-clean, damage-report window, cancellation, key
   handling. The Insureon application currently says no written contracts.
4. **Site claims audit.** "We bring HEPA vacuums / EPA Safer Choice products"
   conflicts with contractors bringing their own equipment. Swap in real
   reviews and real job photos as they come in.
5. **Rewrite the stale W-2 docs** to the 1099 model: `hiring/recruiting-playbook.md`,
   `ops/insurance-and-legal-florida.md`, and the Crew Pack artifact.
6. **Contractor outreach.** Rank `hiring/vetted-cleaners-2026-09-30.csv` by who
   likely carries their own GL insurance; draft messages (don't send).

## Product & infrastructure

7. **No card payments.** Invoiced manually today. Stripe Checkout drops into the
   confirmation step of `api_create_booking` in `server/app.py` (2.9% + $0.30).
8. **Nothing is emailed or texted after booking.** Confirmations only render on
   screen and save to the DB. Same hook point — Postmark/SES + Twilio.
   *Biggest customer-experience win available.*
9. **No database backup.** `data/bookings.db` on the Render disk is the only
   copy of every customer and booking. Enable Render disk snapshots.
10. **Listings.** Yelp pending; Bing Places, Apple Business Connect, Nextdoor to
    add; Google Local Services Ads not applied for. Copy ready in
    `marketing/local-listings.md`. NAP must match exactly everywhere.

## Growth lever
Map-pack ranking follows review volume and recency more than anything on the
site. Target 50+ Google reviews in 90 days; ask by text after every job.
**Never solicit Yelp reviews** — their filter suppresses them and they penalize it.

## Deploy
Push to `main` auto-deploys (~1 min). Fallback: Render → Manual Deploy → Deploy
latest commit. Verify after any GitHub web-UI commit — those can silently fail.
