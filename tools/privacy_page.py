"""Privacy policy (/privacy), rendered by build_site2.py.

Every sentence here has to match what the code actually does, so check it when
any of these change: the /book form fields, server/payments.py (Stripe),
server/notify.py (email + texts), server/tags.py (Pixel, Google tag) and
server/conversions.py (Meta Conversions API, GA4 Measurement Protocol). Meta
requires a published policy before the Pixel runs, and Twilio's A2P 10DLC
review reads the text-message section.

Not yet reviewed by an attorney -- see ops/privacy-policy-attorney-review.md.
"""
from home_v2 import E, final_cta, icon
from inner_v2 import page_hero

EFFECTIVE = "October 27, 2026"

# (heading, [paragraphs or ("ul", [items])]). Plain strings are escaped; the
# few links are added as HTML in the LINKS step below.
def _sections(cfg):
    name = cfg["name"]
    email, phone = cfg["email"], cfg["phone"]
    return [
        ("Who we are", [
            "%s LLC is a home and commercial cleaning business based in Tampa, Florida. "
            "“We” and “us” in this policy mean %s. This policy covers "
            "tampamaidscleaning.com, our booking pages and the texts and emails we send."
            % (name, name),
        ]),
        ("What we collect", [
            "When you get a quote or book, you give us:",
            ("ul", [
                "Your name, phone number and email address.",
                "The service address, city and ZIP code, and any access notes you choose "
                "to add (gate or door codes, parking, pets).",
                "Details of the job: service, home size or square footage, how often, "
                "extras, date and time, notes, and any referral code.",
                "That you accepted our service agreement, and which version.",
            ]),
            "When you use the contact form or the “send me this quote” box, we "
            "collect your name, email, an optional phone number and your message or quote.",
            "If you text or call us, we have your number and what you send us.",
            "If you pay by card, your card details go straight to our payment processor, "
            "Stripe. We never see or store your full card number. We keep a Stripe "
            "customer reference and the payment status so we can charge for a completed "
            "clean or send you a payment link.",
            "Like most websites, our server records basic technical information with each "
            "request, such as your IP address, browser type and the page asked for.",
        ]),
        ("How we use it", [
            ("ul", [
                "To give you a price, book and schedule your clean, and do the work.",
                "To take payment for completed cleans.",
                "To send booking confirmations, reminders, schedule changes and receipts.",
                "To ask for a review after a clean.",
                "To answer your questions and quote requests.",
                "To measure whether our advertising works (see Cookies and ads below).",
                "To keep records we need for taxes and accounting, and to prevent fraud "
                "and abuse of our forms.",
            ]),
        ]),
        ("Who we share it with", [
            "We do not sell your personal information. We share it only as needed to run "
            "the business:",
            ("ul", [
                "The cleaning professional assigned to your job sees your name, phone "
                "number, service address and access notes so they can do the clean.",
                "Stripe processes card payments.",
                "Our email provider delivers our emails, and our text-message provider "
                "(Twilio) delivers our texts.",
                "Our web host stores the site and our booking records.",
                "Meta (Facebook and Instagram) and Google receive advertising and "
                "analytics data when those tools are switched on, as described below.",
                "Authorities, if the law requires it, or to protect our rights or "
                "someone's safety.",
            ]),
            "Our pages also load some photos from Unsplash, an image service, which "
            "receives your IP address when your browser fetches them.",
        ]),
        ("Cookies and ads", [
            "Our own site uses a sign-in cookie (gc_session) only for staff and for "
            "customers who sign in to the app. Your browser's local storage keeps a copy "
            "of our price list and the email you booked with, so the booking tracker can "
            "find your booking. We do not use these for advertising.",
            "When we run ads, we may switch on these tools. When they are on, they set "
            "their own cookies:",
            ("ul", [
                "Meta Pixel (cookies such as _fbp and _fbc): records page views, and when "
                "you book or send us a quote request.",
                "Google tag, Google Analytics 4 and Google Ads (cookies such as _ga, "
                "_ga_* and _gcl_au): measures visits, bookings and quote requests.",
                "When a clean is paid for, our server may also report the sale directly to "
                "Meta (Conversions API) and Google Analytics. For Meta that report includes "
                "your email and phone number in hashed (scrambled) form, the Meta cookie "
                "IDs above, your browser type and the amount. Google receives its "
                "analytics ID and the amount.",
            ]),
            "Meta and Google use this to measure our ads and may use it to show you ads. "
            "Their own privacy policies cover what they do with it.",
            "To opt out: block or delete cookies in your browser settings; change your "
            "Meta ad settings at facebook.com/adpreferences; change your Google ad "
            "settings at myadcenter.google.com; or install Google's Analytics opt-out "
            "add-on from tools.google.com/dlpage/gaoptout. Opting out does not stop you "
            "booking.",
        ]),
        ("Text messages", [
            "If you give us your mobile number and agree to receive texts, we may text "
            "you about your booking: confirmations, reminders, schedule changes, payment "
            "links and a review request. We don't send marketing texts unless you have "
            "separately agreed to them. Message frequency varies with your bookings.",
            "Message and data rates may apply. Reply STOP to any text to stop receiving "
            "them, or HELP for help. You can also contact us at %s or %s." % (phone, email),
            "We do not sell or share your mobile number or your consent to receive texts "
            "with anyone for their own marketing. If you text our number yourself, we "
            "reply from that number.",
        ]),
        ("How long we keep it", [
            "We keep booking, job and payment records while you are a client, and "
            "afterwards for as long as we need them for taxes, accounting, disputes and "
            "other legal obligations. Quote requests and messages from people who don't "
            "book are kept until they are no longer useful or you ask us to delete them.",
        ]),
        ("Your choices and requests", [
            "You can ask to see the personal information we hold about you, to correct "
            "it, or to delete it. Email %s or call %s. We may need to confirm it is you "
            "first. We will delete what we can, but we may keep records the law requires "
            "us to keep, such as payment and tax records." % (email, phone),
            "You can unsubscribe from review-request emails at any time by replying to "
            "say so.",
        ]),
        ("Security", [
            "Our site uses HTTPS, and staff pages need a password. We limit who can see "
            "customer details to people who need them for the job. No system is "
            "completely secure, so we can't promise that information will never be "
            "exposed, but we will tell you if a breach affects you as the law requires.",
        ]),
        ("Children", [
            "Our services are for adults. We do not knowingly collect personal "
            "information from children under 13. If you think a child has given us "
            "their information, contact us and we will delete it.",
        ]),
        ("Changes to this policy", [
            "If we change this policy, we will post the new version here with a new "
            "effective date.",
        ]),
        ("Contact", [
            "%s LLC, Tampa, Florida. Email %s or call or text %s." % (name, email, phone),
        ]),
    ]


LINKS = {
    "facebook.com/adpreferences": "https://www.facebook.com/adpreferences",
    "myadcenter.google.com": "https://myadcenter.google.com",
    "tools.google.com/dlpage/gaoptout": "https://tools.google.com/dlpage/gaoptout",
}


def _para(text):
    h = E(text)
    for label, url in LINKS.items():
        h = h.replace(label, '<a href="%s" rel="noopener" target="_blank">%s</a>' % (url, label))
    return h


def privacy_page(cfg):
    hero = page_hero(
        "Privacy policy",
        "Your information, <em>in plain English.</em>",
        "What we collect when you get a quote or book, why, who sees it, and how to "
        "ask us to delete it.")

    secs = []
    for title, parts in _sections(cfg):
        out = []
        for p in parts:
            if isinstance(p, tuple):
                out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % _para(i) for i in p[1]))
            else:
                out.append("<p>%s</p>" % _para(p))
        # deliberately NOT .rv: a policy must never depend on JS to be readable
        secs.append('<section class="t-sec"><h2>%s</h2>%s</section>' % (E(title), "".join(out)))

    body = (
        '<section class="h-sec" style="padding-top:8px">'
        '<div class="wrap p-faq-grid">'
        '<div class="t-body">'
        '<p class="t-intro">Effective %s.</p>'
        '%s'
        '</div>'
        '<aside class="p-side rv">'
        '<h2>Privacy question?</h2>'
        '<p>Ask us to see, correct or delete your information.</p>'
        '<a class="btn btn-accent" href="mailto:%s" data-biz-href="email">%s<span>Email us</span></a>'
        '<a class="btn btn-ghost" href="tel:%s" data-biz-href="phone">%s<span data-biz="phone">%s</span></a>'
        '</aside></div></section>'
    ) % (EFFECTIVE, "".join(secs), E(cfg["email"]), icon("mail"),
         cfg["phone_raw"], icon("phone"), E(cfg["phone"]))

    return hero + body + final_cta(
        cfg, "Ready when you are.",
        "Flat written price in about a minute. No card, no obligation.")
