# Going live — tampamaidscleaning.com

**Time: about 30 minutes.** Cost: ~$7–8/month (Render). Your GoDaddy domain stays
exactly where it is — you're only changing where it points.

> **Heads up:** a GoDaddy Website Builder site is live at your domain right now.
> Finishing these steps replaces it. Check whether it's part of a GoDaddy plan
> you can cancel afterwards.

---

## Step 1 — Local setup ✅ ALREADY DONE

The repo is initialized and committed. Nothing for you to do here.

Your database, and your `hiring/` and `ops/` documents, are excluded — they stay
on your Mac and never go to GitHub.

---

## Step 2 — Put the code on GitHub (~5 min)

1. Go to **github.com** → sign in (or create a free account).
2. Click **+** (top right) → **New repository**.
3. Name it `tampa-maids`. Choose **Private**.
4. **Do not** tick "Add a README" — leave all the checkboxes empty.
5. Click **Create repository**.
6. GitHub shows a page with commands. Ignore it and run these instead, pasting
   **your** username where shown:

```bash
cd "/Users/nathanieljennings/Cleaning Business"
git remote add origin https://github.com/YOUR-USERNAME/tampa-maids.git
git push -u origin main
```

When it asks for a password, GitHub will **not** accept your account password.
It wants a token: github.com → your avatar → **Settings** → **Developer
settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new
token**, tick the **repo** box, generate, copy it, and paste that as the
password.

*(Easier alternative: install GitHub Desktop, sign in, and use "Add existing
repository" → publish. Same result, no token.)*

---

## Step 3 — Deploy on Render (~10 min)

1. Go to **render.com** → **Get Started** → sign in with GitHub.
2. Click **New** → **Blueprint**.
3. Pick your `tampa-maids` repo. Render reads `render.yaml` and sets everything
   up, including the storage disk.
4. Before you confirm, it asks for two values. Set them:

   | Key | What to put |
   |---|---|
   | `OWNER_EMAIL` | `you@tampamaidscleaning.com` (or your Gmail for now) |
   | `OWNER_PASSWORD` | A long password you invent. **Write it down.** |

   This becomes your dashboard login.

5. Click **Apply** and wait for the build (2–5 min).
6. You'll get a URL like `https://tampa-maids-cleaning.onrender.com`. **Open it.
   The site should load.** Add `/admin` and sign in with the email and password
   from step 4.

> ⚠️ **Do not pick the free plan.** It has no permanent storage, so every update
> would erase all your customers and bookings. The blueprint already selects the
> paid one.

If the site loads, the hard part is over. Everything after this is just pointing
your domain at it.

---

## Step 4 — Connect your domain (~5 min + waiting)

**In Render:**

1. Open your service → **Settings** → **Custom Domains**.
2. Add `tampamaidscleaning.com`, then add `www.tampamaidscleaning.com`.
3. Render now shows you the DNS records to create. **Leave this tab open** —
   you'll copy from it. It gives you:
   - an **A record** value (an IP address) for the root domain
   - a **CNAME record** value (ends in `.onrender.com`) for `www`

   Use the values on your screen. They're specific to your service.

**In GoDaddy:**

4. Sign in → find `tampamaidscleaning.com` → open its **DNS** settings.
   (GoDaddy moves this around; look for **DNS** or **Manage DNS**.)
5. **Delete the existing records first.** You'll see an `A` record named `@` and
   usually a `CNAME` named `www`, pointing at GoDaddy's website builder. Delete
   or edit both. If GoDaddy warns that a site is connected, that's the Airo site
   — disconnecting it is what you want.
6. Add these two, using the values from your Render tab:

   | Type | Name | Value | TTL |
   |---|---|---|---|
   | A | `@` | the IP Render showed you | 600 |
   | CNAME | `www` | the `...onrender.com` host Render showed you | 600 |

7. Save.

---

## Step 5 — Wait, then check

Usually **10–30 minutes**; GoDaddy can take a few hours.

- In Render, the domains flip to **Verified**, then it issues your HTTPS
  certificate automatically.
- A security warning during the first hour is normal. It clears itself.

Check from your Mac any time:

```bash
dig +short tampamaidscleaning.com
```

When that prints the IP Render gave you instead of `76.223.105.230`, it worked.

Then open **https://tampamaidscleaning.com**. You're live.

---

## Step 6 — Email (separate, do whenever)

Your site publishes `hello@tampamaidscleaning.com`, which doesn't exist yet.
There are no MX records on the domain, so mail sent there bounces.

- **Cheapest:** GoDaddy Email Forwarding — forwards to your Gmail.
- **Proper:** Google Workspace, ~$7/month — a real mailbox you can send from.

Either way you add MX records in the same GoDaddy DNS screen. MX records don't
interfere with the A and CNAME records above.

---

## Before you tell anyone the address

- [ ] **Replace the six testimonials** in `business.json`. They're placeholder
      copy I wrote to show the layout. Publishing invented reviews is deceptive
      and an FTC matter.
- [ ] **Set a real phone number** — `(727) 555-0142` is a placeholder, and an
      813 number suits a Tampa business.
- [ ] Submit `https://tampamaidscleaning.com/sitemap.xml` to Google Search
      Console.
- [ ] Create Google Business Profiles for Tampa, St. Pete, Clearwater and
      Sarasota, each pointing at its `/cleaning/<city>` page.
- [ ] Turn on disk snapshots in Render. Your bookings live nowhere else.

---

## Updating the site later

Change anything (prices in `business.json`, copy, whatever), then:

```bash
cd "/Users/nathanieljennings/Cleaning Business"
python3 tools/build_site.py && python3 tools/build_site2.py
python3 tools/build_book.py && python3 tools/build_markets.py
git add -A && git commit -m "Update prices"
git push
```

Render redeploys automatically in a couple of minutes. Your bookings and
customers are on the storage disk and survive every deploy.

---

## Not built yet

- **No card payments.** Bookings are invoiced manually, matching your plan's
  "charged on the day of service" model.
- **No automatic emails or texts.** Confirmations show on screen and are stored,
  but nothing is sent.

Both hook into `api_create_booking` in `server/app.py` when you want them.

---

## If something breaks

| Problem | Fix |
|---|---|
| Render build fails | Open the build log; it names the failing line. |
| Site loads but `/admin` won't accept your login | `OWNER_EMAIL`/`OWNER_PASSWORD` weren't set before first boot. Set them in Render → Environment, then **Manual Deploy → Clear build cache & deploy**. |
| Domain still shows the old GoDaddy site | Old DNS records weren't deleted, or you're seeing a cached copy. Recheck step 4.5, then try a private browsing window. |
| "Not secure" warning | Certificate hasn't issued yet. Wait for Render to show **Verified**. |
| Lost your dashboard password | Change `OWNER_PASSWORD` in Render → Environment and redeploy. |
