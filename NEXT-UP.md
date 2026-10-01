# Next up — Tampa Maids Cleaning

Accurate as of 2026-10-01, 01:50 ET. Everything in "Blocked on you" genuinely
cannot be done by Claude — it needs your accounts, your money or your decision.

## Blocked on you (nothing moves until these do)

1. **Bind the insurance.** Insureon BOP $938/yr, quote expires ~Oct 30. The
   site tells customers "fully insured before your first clean" on 64 pages.
   That promise is live and unbacked while bookings are open.
2. **Set the contractor pay rate.** Deliberately blank in the agreement. Tampa
   1099 cleaners run $22–35/hr equivalent, or price at 50–55% of the job. The
   agreement and your job ads must use the same number.
3. **Florida attorney review** of the contractor agreement, the FCRA
   background-check form and the client service agreement (/terms).
4. **Mail provider key** to switch confirmations on. Add to Render →
   Environment: `POSTMARK_TOKEN` + `MAIL_FROM`, optionally `OWNER_NOTIFY`.
   MAIL_FROM must be an address the provider has verified for the domain.
5. **Create hello@tampamaidscleaning.com.** The site publishes it; no mailbox
   exists, and it is what MAIL_FROM should be.
6. **Decide on the (571) number.** Northern Virginia area code on a Tampa
   business. Customers and local ranking both read area code as locality.
   Changing it means re-verifying the Google profile.
7. **Google Search Console** — submit /sitemap.xml (42 urls).
8. **Yelp, Nextdoor Business Page, Angi** — content ready in
   marketing/local-listings.md.
9. **Real job photos** to replace stock, and **real reviews**. Reviews are the
   single biggest lever on map-pack ranking and can only come from real cleans.
   `business.json.testimonials` is empty by design; add entries with
   `"verified": true` only when a customer actually wrote them.

## Built and waiting on the above
- Booking confirmation emails — fail-safe, logs until a provider key is set.
- `/review` 302 for the printed QR cards; target in `business.json.review_url`.
- Owner-only data backups, dashboard → "Your data".
- Client service agreement enforced at booking, version + timestamp + IP
  recorded per booking.

## Not built
- **Card payments.** Invoiced manually, matching the "charged on the day of
  service" model. Stripe Checkout drops into `api_create_booking`.
- **SMS.** Same hook point; Twilio.

## Known and accepted
- Every Render deploy causes ~30–60s of 502s. Cause is the persistent disk
  (one instance can mount it at a time), NOT a missing health check — that is
  already set to /api/config. Only fix is moving to Postgres and dropping the
  disk. Don't push while demoing the site.

## Automation running
- 01:40 daily — hot leads sweep (Chrome, read-only, never contacts anyone)
- 07:41 daily — lead + contact sweep *(overlaps the 01:40 one; consider
  disabling one)*
- 20:52 daily — improvement pass + refreshes the Command Center

## Audit state
Last full check 2026-10-01: 42/42 sitemap urls live, zero broken links across
2,024 internal links, all images have alt text, structured data valid on every
page type, self-hosted fonts, 36KB homepage at 0.37s TTFB, booking and terms
enforcement verified in production. No known defects.
