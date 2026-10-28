# TODAY: calls that make money (Wed Oct 28, 2026)

Everything below is already written. Open the file, dial, read. Log each call in the Command Center ("Mark sent") so nobody gets called twice. Calls from your phone to people who posted publicly are fine; **no cold texts** (Florida FTSA).

## 0. 9:00 AM — Elite Business Insurance, **(813) 922-3055**, ask for Stephen Ifasi (5 minutes)
Pay to bind the ERGO NEXT general liability policy, **$63.58/mo**, plus the **$25k janitorial bond ($165/yr)**. Have a debit card or routing + account number ready. Full checklist: `ops/elite-payment-call.md`. On the call confirm: uninsured 1099 cleaners covered; primary & non-contributory wording; **commercial cleaning added to the business description** (still unanswered by email); coverage starts today. Ask him to email the policy number, declarations page, a sample COI and the bond certificate.

**Why first:** 11 of the biggest calls below (lease-ups, builders, the TPA hangar, the clinic) want a certificate of insurance before they put you on a vendor list. After this call you can say "insured" on every other call today, and tell Claude "insurance is paid" so the site switches to "fully insured" (one line in business.json, see INSURANCE-GO-LIVE.md).

## 1. Jennings Media: listing agents with no video (free 30-second reel pitch, then volume rate)
Pitch for all of them: *"Hi <name>, it's Nate with Jennings Media in Tampa. You've got N listings up right now and none has a video. I'd like to make a free 30-second reel for one so you can see the work. If you like it, I'll do the rest at a volume rate. Which listing should I start with?"*

| # | Who | Phone | Why |
|---|---|---|---|
| 1 | Cory Jursik, Shore Property | 727-742-1828 | 8 no-video listings, $18.2M (Indian Rocks Beach) |
| 2 | Gregory Margliano, Compass | 813-365-9935 | 3 no-video listings, $12.7M (4201 Bayshore #2101 $7M) |
| 3 | Myles Newell, VCWB Development | 386-503-3389 | $11.95M Clearwater Beach penthouse, no video; developer = whole building |
| 4 | Anna Dementov, Florida Luxury | 727-488-4825 | 4 no-video listings, $10.1M (IG DM sent 10/13, no reply: call) |
| 5 | Julie Folden, Coastal Properties | 727-493-1555 | 2 no-video listings, $9.3M |
| 6 | Selviye Tzekas, Engel & Völkers | 727-461-1000 | 3 no-video listings, $8.0M |
| 7 | Sarena Irwin, Smith & Associates | 727-342-3800 | 2 no-video listings, $7.9M |
| 8 | Ana Chirino, Chirino | 813-642-3325 | 2 no-video listings, $7.4M |
| 9 | Mary Beth Byrd, Smith & Associates | 813-839-3800 | 2 no-video listings, $7.3M |
| 10 | Jeffrey Beggins, Century 21 Beggins (broker) | 727-596-3343 | 4 of his own + ~32 agents: pitch an office rate |

New this week (Redfin, newest $750K+ in Tampa): see the "Fresh listings" section at the bottom once filled in.

## 2. Tampa Maids: commercial and recurring (say "insured" only after call #0)
| # | Who | Phone | Script id in Command Center | Est. value |
|---|---|---|---|---|
| 11 | LifeWorks Wellness Center, new building, 375 Turner St | (727) 466-6789 | o-call-tm-med-lifeworks-wellness-center-new-treatm | ~100-staff clinic, nightly clean, $2–4k/mo |
| 12 | FlyUSA, new 50,000 sf hangar at TPA | (727) 325-5957 | o-call-tm-flyusa-hangar | recurring lounge/office clean |
| 13 | SkyRun Vacation Rentals, Anna Maria | 941-799-1128 | o-call-tm-skyrun-ami | turnovers $95–180 each, snowbird season |
| 14 | Seazen Rocky Point (ZRS), ask for Kristen, PM | 813-419-1931 | o-tm-com-seazen-rocky-point-tampa-waterfront-no | $1.5–4k/mo turns |
| 15 | Town Westshore (Marina Pointe) | (813) 694-5224 | o-tm-com-town-westshore-marina-pointe-tampa-ope | $1.5–4k/mo turns |
| 16 | Cobalt Apartments, ask for Jessica Moats | (813) 364-8832 | o-tm-com-cobalt-apartments-lutz-wesley-chapel-l | $1.5–4k/mo turns |
| 17 | Brea Lakewood Ranch | (941) 393-0676 | o-tm-com-brea-lakewood-ranch-brand-new-communit | $1.5–3.5k/mo turns |
| 18 | Solé at Brandon (ZRS), ask for Dana Swint | 877-708-2296 | o-tm-com-sol-at-brandon-riverview-now-leasing | $1–3k/mo turns |
| 19 | Enclave at Wesley Chapel | (813) 692-9761 | o-tm-call-com-enclave-at-wesley-chapel-1014 | turns, backup vendor |
| 20 | The Parian, Riverview | (813) 213-3857 | o-tm-call-com-the-parian-riverview-1014 | turns, backup vendor |

Script for 14–20 (apartment turns): *"Hi, this is Nate Jennings with Tampa Maids Cleaning here in Tampa Bay. I'm calling for whoever handles make-ready and turnover cleaning. We do move-out and make-ready cleans at flat prices by unit size, with before-and-after photos of every room so your team doesn't walk each unit, and a free re-clean within 24 hours. Who should I send a per-unit rate sheet to?"* If they ask for a COI: "Yes, I'll have it to you today" (only after call #0).

## 3. Jennings Media: events and lease-up marketing
| # | Who | Phone | Why |
|---|---|---|---|
| 21 | ClearView at Echelon City Center (ZRS), St. Pete | (727) 617-5053 | 363-unit lease-up; reels + Meta ads to fill units |
| 22 | TIDES summit, Nov 16–17, Tampa Convention Center | (813) 263-8177 | first-year summit recap film (IG DM 10/13 unanswered) |
| 23 | Neal Communities (hiring a content specialist) | (888) 720-4429 | monthly retainer instead of a hire |

## After the calls
- 64 B2B emails are ready in `marketing/send-emails-2026-10-28.html` (one click each opens a prefilled Gmail draft), or paste a Gmail app password into Render and run `python3 tools/send_outreach.py --send` to send them all in ~6 minutes. Steps: `ops/turn-on-email.md`.
- Voicemail (all calls): "Hi, this is Nathaniel Jennings with Tampa Maids Cleaning / Jennings Media in Tampa. Please call me back at (571) 317-3211. Thanks."

## Fresh listings (Redfin, newest $750K+ in Tampa, checked Oct 28)
Same pitch as section 1. Smith & Associates' South Tampa office line is 813-839-3800: ask for the agent by name.

| # | Who | Phone | Why |
|---|---|---|---|
| 24 | **Stephen Gay**, Smith & Associates | 813-839-3800 | **924 S Golf View St, $19.95M, listed this week, NO video**; also 905 S Bruce ($1.495M, no video) and 1505 S Howard ($1.95M). Call him first. |
| 25 | Fausto Rodriguez, Barnes International (Miami) | 305-361-2233 | 3101 Bayshore #1503, $3.295M, no video; needs a local crew |
| 26 | Anne Mullis, Smith & Associates | 813-839-3800 | 2419 Bayshore 3N, $2.5M, no video (2N at $1.999M likely hers too) |
| 27 | Kristen Arseneau, Smith & Associates | 813-839-3800 | 4418 W Kensington, $1.55M, no video |
| 28 | Bill Gramatica, Charles Rutenberg | 866-580-6402 | 14623 Canopy Dr, $1.45M |

Skipped: 5823 Bowen Daniel #704 (Ken Peterson) already has video.
