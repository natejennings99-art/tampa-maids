# Go live — no terminal needed

Everything is already packaged. You'll drag a folder into a website, click
through two signups, and type two DNS records. About 25 minutes.

**Your files to upload are in the `_upload` folder** inside
`/Users/nathanieljennings/Cleaning Business/`.

> A GoDaddy Website Builder site is live at your domain right now. Finishing
> this replaces it.

---

## 1. Upload to GitHub (~7 min)

1. Go to **github.com** and sign up (free) or sign in.
2. Click the **+** in the top right → **New repository**.
3. Repository name: `tampa-maids`
4. Select **Private**.
5. Leave every checkbox unticked. Click **Create repository**.
6. On the next page, click the link that says
   **"uploading an existing file"**.
7. Open a Finder window at
   `/Users/nathanieljennings/Cleaning Business/_upload`
8. Press **⌘A** to select everything inside it, then **drag it all** into the
   GitHub page.

   *Drag the contents, not the `_upload` folder itself.* You should see
   `Dockerfile`, `business.json`, `render.yaml`, `run.sh`, `server`, `tools`,
   `web` and the two `.md` files.

9. Wait for the uploads to finish, then click **Commit changes**.

Done — no terminal, no password token.

---

## 2. Deploy on Render (~10 min)

1. Go to **render.com** → **Get Started** → **Sign in with GitHub** → allow
   access when asked.
2. Click **New** → **Blueprint**.
3. Choose your `tampa-maids` repository.
4. Render reads the settings file and shows two blanks to fill in:

   | Field | What to enter |
   |---|---|
   | `OWNER_EMAIL` | your email address |
   | `OWNER_PASSWORD` | a password you make up — **write it down** |

   This becomes your dashboard login.

5. Click **Apply**. Wait 3–5 minutes while it builds.
6. It gives you a link like `tampa-maids-cleaning.onrender.com`.
   **Click it — your site should load.**

Add `/admin` to that link and sign in with the email and password from step 4
to check the dashboard works.

> Don't switch to the free plan. It has no permanent storage, so every update
> would erase your bookings. The settings file already picks the right one
> (about $7/month).

**If the site loads, the hard part is over.**

---

## 3. Point your domain at it (~5 min)

**First, in Render:**

1. Open your service → **Settings** → **Custom Domains**.
2. Add `tampamaidscleaning.com`. Add `www.tampamaidscleaning.com` too.
3. Render now displays the two values you need. **Keep this tab open.**

**Then, in GoDaddy:**

4. Sign in → find `tampamaidscleaning.com` → open its **DNS** page.
5. **Delete what's already there** — an `A` record named `@` and usually a
   `CNAME` named `www`. They point at GoDaddy's website builder. If GoDaddy
   warns that a site will be disconnected, that's expected.
6. Add two new records, copying the values from your Render tab:

   | Type | Name | Value | TTL |
   |---|---|---|---|
   | A | `@` | the IP address Render showed | 600 |
   | CNAME | `www` | the `...onrender.com` address Render showed | 600 |

7. Save.

---

## 4. Wait

Usually 10–30 minutes. GoDaddy can take a few hours.

Render will show your domains as **Verified**, then turn on HTTPS by itself.
A "not secure" warning in the first hour is normal and fixes itself.

Then open **https://tampamaidscleaning.com**.

---

## Changing things later

Edit prices, wording or hours in `business.json`, then ask Claude to rebuild.
To publish: go to your GitHub repo → **Add file** → **Upload files** → drag the
changed files → **Commit**. Render updates itself within a couple of minutes.

Your customers and bookings live on Render's storage disk and survive every
update.

---

## Before you hand out the address

- [ ] **Replace the six testimonials** in `business.json`. They're placeholder
      copy written to show the layout, not real reviews.
- [ ] **Put in a real phone number** — `(727) 555-0142` is a placeholder.
- [ ] Turn on disk snapshots in Render. Your bookings exist nowhere else.

---

## If you get stuck

| What you see | What to do |
|---|---|
| Render build fails | Open the log, copy the red lines, send them to Claude. |
| `/admin` won't take your password | The two fields in step 2.4 weren't saved. In Render → **Environment**, set them, then **Manual Deploy → Clear build cache & deploy**. |
| Domain still shows the old GoDaddy site | Old DNS records are still there. Redo step 3.5. Try a private browsing window. |
| "Not secure" warning | Certificate hasn't issued yet. Wait for **Verified** in Render. |
