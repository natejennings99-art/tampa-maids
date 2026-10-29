# Next up — Tampa Maids Cleaning

Accurate as of 2026-10-29. Ranked by money. Everything in "Blocked on you" needs
your accounts, your money, your phone or your decision; Claude can't do them.

## Blocked on you

1. **Call Stephen at Elite to bind insurance (10 min, today).** GL $63.58/mo +
   $25k bond $165/yr, already accepted. The quote window ends around Oct 30.
   Until it's bound, every booking is an uninsured job.
2. **Gmail app password into Render (5 min).** `ops/turn-on-email.md`. This one
   key switches on booking confirmations, reminders, next-visit emails, pay
   links, owner alerts by email, and `tools/send_outreach.py`, which can send
   the ~900 queued outreach emails (10 sent so far). Without it a real booking
   lands silently.
3. **Send outreach.** Either run `python3 tools/send_outreach.py --send --limit 20`
   once the password is in, or click through `marketing/send-emails-<date>.html`.
   Work today's call sheet `TODAY-CALLS-<date>.md`. This is the only near-term
   source of revenue; inbound is still ~0.
4. **Reply to Ultim8 (Chris).** An insured sub partner with a COI naming us. Their
   rates work on one-time, deep and move-out jobs. Biweekly needs their recurring
   rate (asked 10/27). Signing a partner is what lets the 2-jobs/day cap rise.
5. **Stripe key into Render (15 min).** `ops/run-it-from-your-phone.md` §2. Test
   with `sk_test_…` and `/book?testpay=1`, then swap in the live key. Cards are
   saved at booking and charged when the job is marked done.
6. **Texts (Twilio, or free email-to-text).** Same guide, §3. New bookings,
   payments, skips/pauses/plan endings and the 7 AM schedule then reach your phone.
7. **Ad IDs (only when you run ads).** `META_PIXEL_ID`, `GOOGLE_TAG_ID`,
   `GOOGLE_ADS_ID` (+ labels), `META_CAPI_TOKEN`, `GA_API_SECRET`.
8. **Decide the late-cancellation fee amount.** The policy says "a fee applies"
   but names no amount, so nothing can charge it.
9. **Attorney review** of the contractor agreement, FCRA form, /terms and
   /privacy (questions in `ops/privacy-policy-attorney-review.md`).
10. **Render disk snapshots** (Render dashboard → Disk). The database is the
    only copy of every customer; owner downloads exist at /admin → Your data.
11. **Real reviews and job photos** after the first cleans. `/review` and the QR
    card are ready. Never filter who gets asked.
12. **(571) area code** on a Tampa business: your call (changing it means
    re-verifying the Google profile).

## Built and waiting on the keys above
- /owner phone page: today/tomorrow jobs, unpaid invoices (charge, pay link,
  mark paid), Friday cleaner payouts + 1099 totals, recurring plans (stalled
  rebook, ended-plan call list).
- Card on file → charged on completion, pay-link fallback, Stripe webhook.
- Recurring plans book their own next visit; customers can skip, pause 2/4
  weeks, reschedule, or switch a one-time clean to a plan on /track.
- Day-before reminders, owner texts, 7 AM daily schedule text.
- Meta Pixel / Google tag + server-side purchase events, off until IDs are set.
- SMS opt-in on /book, privacy policy, client service agreement at booking.

## Known and accepted
- Every Render deploy causes ~30–60s of 502s (persistent disk; one instance
  mounts it at a time). Don't push while demoing.
- Capacity caps (1 job/slot, 2/day) stay until a contractor or partner signs;
  tests enforce them.
