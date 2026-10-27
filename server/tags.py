"""Ad and analytics tags (Meta Pixel, Google tag), switched on by env vars.

Nothing loads unless an ID is set, so the site stays tag-free by default.
The server injects the snippet into every public HTML page just before
</head>. The libraries load async, and the stubs queue any events fired
before they arrive.

  META_PIXEL_ID               digits, e.g. 123456789012345
  GOOGLE_TAG_ID               GA4 measurement ID, G-XXXXXXX (or a GT- tag)
  GOOGLE_ADS_ID               AW-123456789, optional
  GOOGLE_ADS_LEAD_LABEL       conversion label for a booking/quote, optional
  GOOGLE_ADS_PURCHASE_LABEL   conversion label for a payment, optional

IDs are validated against their published formats and ignored otherwise,
because they are written into a <script> on every page.
"""
import hashlib, json, os, re

_META_RX = re.compile(r"^\d{6,20}$")
_GTAG_RX = re.compile(r"^(G|GT|AW)-[A-Z0-9]{4,20}$")
_LABEL_RX = re.compile(r"^[A-Za-z0-9_-]{4,40}$")

# Staff pages are never tagged: Nate's own visits are not leads.
UNTAGGED_PREFIXES = ("admin/", "owner", "app/")


def _env(k, rx):
    v = os.environ.get(k, "").strip()
    return v if rx.match(v) else ""


def config():
    ads = _env("GOOGLE_ADS_ID", _GTAG_RX)
    return {
        "meta": _env("META_PIXEL_ID", _META_RX),
        "ga": _env("GOOGLE_TAG_ID", _GTAG_RX),
        "ads": ads if ads.startswith("AW-") else "",
        "leadLabel": _env("GOOGLE_ADS_LEAD_LABEL", _LABEL_RX),
        "purchaseLabel": _env("GOOGLE_ADS_PURCHASE_LABEL", _LABEL_RX),
    }


def snippet(cfg=None):
    c = cfg or config()
    if not (c["meta"] or c["ga"] or c["ads"]):
        return ""
    parts = ["<script>window.TM_TAGS=%s;</script>" % json.dumps(c, separators=(",", ":"))]
    first_google = c["ga"] or c["ads"]
    if first_google:
        parts.append(
            '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>'
            "<script>window.dataLayer=window.dataLayer||[];"
            "function gtag(){dataLayer.push(arguments);}gtag('js',new Date());%s</script>"
            % (first_google, "".join("gtag('config','%s');" % i for i in (c["ga"], c["ads"]) if i)))
    if c["meta"]:
        parts.append(
            "<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?"
            "n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;"
            "n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;"
            "t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}"
            "(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
            "fbq('init','%s');fbq('track','PageView');</script>" % c["meta"])
    return "".join(parts)


def inject(html_bytes, rel_path):
    """Return (bytes, etag_suffix). The suffix changes when the tag config
    does, so a browser holding an untagged page's ETag gets the new one."""
    if rel_path.startswith(UNTAGGED_PREFIXES):
        return html_bytes, ""
    s = snippet()
    if not s:
        return html_bytes, ""
    i = html_bytes.lower().find(b"</head>")
    if i < 0:
        return html_bytes, ""
    return (html_bytes[:i] + s.encode() + html_bytes[i:],
            "-" + hashlib.sha1(s.encode()).hexdigest()[:8])
