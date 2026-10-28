#!/usr/bin/env python3
"""Build marketing/send-emails-<date>.html: one card per sendable outreach
email with an Open-in-Gmail button (prefilled to/subject/body), a mailto
fallback, Copy, and a Sent tick kept in localStorage. No app password needed:
Nate clicks Open, Gmail opens the draft, he presses Send."""
import datetime
import html
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outreach_mail as om  # noqa: E402

ROOT = om.ROOT
TODAY = datetime.date.today().isoformat()
OUT = os.path.join(ROOT, "marketing", "send-emails-%s.html" % TODAY)

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Send emails today</title>
<style>
:root{--bg:#f3f6f5;--card:#fff;--fg:#14302f;--muted:#5b706e;--line:#d6e0de;--teal:#0f5257;--gold:#d99a2b;--gold-ink:#3a2706;--done:#2f7a4f;--done-bg:#e3f1e8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d1a1a;--card:#142424;--fg:#e4eeec;--muted:#93a9a6;--line:#25393a;--teal:#5fb7b9;--gold:#e8b04d;--gold-ink:#2a1c03;--done:#6fcf97;--done-bg:#16301f;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0d1a1a;--card:#142424;--fg:#e4eeec;--muted:#93a9a6;--line:#25393a;--teal:#5fb7b9;--gold:#e8b04d;--gold-ink:#2a1c03;--done:#6fcf97;--done-bg:#16301f;color-scheme:dark}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Public Sans",sans-serif}
.wrap{max-width:760px;margin:0 auto;padding:20px 16px 60px}
h1{font-size:clamp(24px,5vw,34px);margin:0;color:var(--teal)}
header p{color:var(--muted);margin:6px 0 0}
.bar{position:sticky;top:0;z-index:2;background:var(--bg);padding:12px 0;margin:14px 0 6px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px}
.meter{flex:1;height:8px;border-radius:99px;background:var(--line);overflow:hidden}.meter i{display:block;height:100%;width:0;background:var(--done)}
.count{font-weight:600;font-variant-numeric:tabular-nums}
h2{font-size:20px;margin:26px 0 4px}h2+p{margin:0 0 12px;color:var(--muted)}
ol{list-style:none;padding:0;margin:0;display:grid;gap:12px}
li{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;display:grid;gap:10px;min-width:0}
li.sent{background:var(--done-bg);border-color:var(--done)}
.top{display:flex;gap:10px;align-items:flex-start}.n{font-size:20px;color:var(--teal);min-width:1.6em}
.who{flex:1;min-width:0}.who b{display:block}.meta{color:var(--muted);font-size:13px;overflow-wrap:anywhere}
.tag{font-size:12px;font-weight:600;background:var(--gold);color:var(--gold-ink);padding:2px 8px;border-radius:99px;white-space:nowrap}
textarea{width:100%;box-sizing:border-box;min-height:120px;font:inherit;font-size:14px;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px;resize:vertical}
.acts{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn{font:inherit;font-weight:600;font-size:14px;border-radius:8px;padding:8px 14px;border:1px solid var(--teal);cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;color:var(--teal);background:transparent}
.open{background:var(--teal);color:var(--bg)}
.mark{margin-left:auto;display:flex;gap:6px;align-items:center;font-size:14px;cursor:pointer}
.btn:focus-visible,textarea:focus-visible,input:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.note{background:#fff3df;color:#7a4500;border-radius:8px;padding:10px 12px;margin-top:12px}
</style></head><body><div class="wrap">
<header><h1>Send these emails today</h1>
<p>Built __TODAY__ from the Command Center queue. For each card: <b>Open in Gmail</b> opens a prefilled draft in a new tab, read it once, press Send, then tick <b>Sent</b>. The mailing address and opt-out line are already in every footer (CAN-SPAM). Tampa Maids B2B first (recurring money), then Jennings Media.</p>
<p class="note">Faster: paste a Gmail app password into Render (ops/turn-on-email.md) and run <code>python3 tools/send_outreach.py --send</code>. It sends all of these in about 6 minutes and marks them sent in the Command Center.</p>
</header>
<div class="bar"><span class="count" id="count">0 of 0 sent</span><div class="meter"><i id="fill"></i></div></div>
<h2>Tampa Maids</h2><p>Property managers, builders, STR managers, schools and offices.</p><ol id="tm"></ol>
<h2>Jennings Media</h2><p>Launch content, events, venues and listing films.</p><ol id="jm"></ol>
</div>
<script>
const DATA=__DATA__;
const KEY="send-emails-__TODAY__";
let sent={};try{sent=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(sent))}catch(e){}}
function el(t,c,txt){const e=document.createElement(t);if(c)e.className=c;if(txt!=null)e.textContent=txt;return e}
function render(){DATA.forEach((d,k)=>{
  const li=el("li");li.id="i-"+d.id;
  const top=el("div","top");top.append(el("span","n",String(k+1)));
  const who=el("div","who");who.append(el("b",null,d.name));who.append(el("span","meta",d.to+" · "+d.subject+(d.exp?" · by "+d.exp:"")));
  top.append(who);top.append(el("span","tag",d.biz==="tm"?"Tampa Maids":"Jennings Media"));
  const ta=el("textarea");ta.readOnly=true;ta.value=d.body;ta.setAttribute("aria-label","Email "+(k+1));
  const acts=el("div","acts");
  const a=el("a","btn open","Open in Gmail");a.href=d.gmail;a.target="_blank";a.rel="noopener";
  const m=el("a","btn","Mail app");m.href=d.mailto;
  const c=el("button","btn","Copy");c.type="button";
  c.onclick=()=>{const done=()=>{c.textContent="Copied";setTimeout(()=>c.textContent="Copy",1500)};
    if(navigator.clipboard){navigator.clipboard.writeText("Subject: "+d.subject+"\\n\\n"+d.body).then(done,()=>ta.select())}else{ta.select()}};
  const lab=el("label","mark");const cb=el("input");cb.type="checkbox";cb.checked=!!sent[d.id];
  cb.onchange=()=>{sent[d.id]=cb.checked;save();li.classList.toggle("sent",cb.checked);tally()};
  lab.append(cb,document.createTextNode("Sent"));
  acts.append(a,m,c,lab);li.append(top,ta,acts);
  if(sent[d.id])li.classList.add("sent");
  document.getElementById(d.biz==="tm"?"tm":"jm").append(li);});tally()}
function tally(){const n=DATA.filter(d=>sent[d.id]).length;document.getElementById("count").textContent=n+" of "+DATA.length+" sent";document.getElementById("fill").style.width=(DATA.length?100*n/DATA.length:0)+"%"}
render();
</script></body></html>
"""


def main():
    ready, skipped = om.sendable()
    rows = []
    for r in ready:
        q = urllib.parse.urlencode({"view": "cm", "fs": "1", "to": r["to"], "su": r["subject"], "body": r["body"]}, quote_via=urllib.parse.quote)
        gmail = "https://mail.google.com/mail/?" + q
        mailto = "mailto:%s?%s" % (r["to"], urllib.parse.urlencode({"subject": r["subject"], "body": r["body"]}, quote_via=urllib.parse.quote))
        rows.append({"id": r["id"], "biz": r["biz"], "to": r["to"], "name": r["name"], "subject": r["subject"],
                     "body": r["body"], "exp": r["exp"], "gmail": gmail, "mailto": mailto})
    data = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(PAGE.replace("__TODAY__", TODAY).replace("__DATA__", data))
    print("wrote %s: %d cards (%d tm, %d jm), %d skipped" % (
        os.path.relpath(OUT, ROOT), len(rows), sum(r["biz"] == "tm" for r in rows), sum(r["biz"] == "jm" for r in rows), len(skipped)))


if __name__ == "__main__":
    main()
