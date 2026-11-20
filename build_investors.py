"""Build one SEO page per investor, an investors index, and add them to sitemap.xml.

Run after build_pages.py, from this folder:  python3 -I build_investors.py
Reads index.html (D, CAT, STAGE, STG, TERMS, PEOPLE, LEADS, WOMEN), founders-slugs.js,
fund-linkedin.json and fund-websites.json (verified only), people-linkedin.json (verified only).
Anything not verified gets a LinkedIn search link, never a guessed URL.
"""
import html
import json
import re
import unicodedata
import urllib.parse
from datetime import date
from pathlib import Path

BASE = "https://angiecarrillo.github.io/latam-founders-map/"
ROOT = Path(__file__).resolve().parent
TODAY = date.today().isoformat()
HOME_LINK = ""  # set by sync_mai.py to add a link back to the Miss Angel Investor home

INDEX = (ROOT / "index.html").read_text()
D = [l.split("|") for l in re.search(r"const D=`\n(.*?)`", INDEX, re.S).group(1).strip().split("\n")]
grab = lambda name: json.loads(re.search(rf"const {name}=(\{{.*?\}});\n", INDEX).group(1))
STAGE, TERMS, PEOPLE, LEADS = grab("STAGE"), grab("TERMS"), grab("PEOPLE"), grab("LEADS")
CAT = dict(re.findall(r'(\w+):"([^"]+)"', re.search(r"const CAT=\{(.*?)\};", INDEX).group(1)))
STG = dict(re.findall(r'(\w):"([^"]+)"', re.search(r"const STG=\{(.*?)\};", INDEX).group(1)))
WOMEN = set(json.loads(re.search(r"const WOMEN=new Set\((\[.*?\])\)", INDEX).group(1)))
FSLUG = json.loads(re.search(r"window\.FSLUG=(\{.*?\});", (ROOT / "founders-slugs.js").read_text()).group(1))
load = lambda f: json.loads((ROOT / f).read_text()) if (ROOT / f).exists() else {}
FLI, FWEB, PLI = load("fund-linkedin.json"), load("fund-websites.json"), load("people-linkedin.json")
e = lambda s: html.escape(str(s), quote=True)

GENERAL = [
    ("Aurora’s 100-VC list", "https://www.auroratechaward.com/vc-list"),
    ("LAVCA’s Top & Emerging Women Investors in Latin America", "https://www.lavca.org/"),
    ("public funding announcements", None),
]


def slugify(name):
    s = unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


inv, used = [], set()
for row in D:
    n, t, k = row[0], row[1], row[2]
    slug = slugify(n) or "investor"
    while slug in used:
        slug += "-2"
    used.add(slug)
    inv.append({"n": n, "t": t, "k": k, "slug": slug})
ISLUG = {i["n"]: i["slug"] for i in inv}

PART = {"de", "da", "do", "dos", "das", "del", "la", "los", "las", "van", "von", "der", "y", "e", "di", "le"}
SKIP = re.compile(r"^(Backed:|LAVCA|Harlem|Open|No |No-|Idea|Pre|Seed|Series|\$|Check|Leads|Up to|Equity|Grant|Prize|Programs?|Applications?|Up )")
norm = lambda s: re.sub(r"[^a-z]", "", unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower())


def is_name(n):
    w = n.split()
    return 2 <= len(w) <= 7 and not re.search(r"[\d$&/():;]", n) and all(x[0].isupper() or x in PART for x in w)


def split_people(fund):
    """Contact line -> (people [(name, title)], founders [(name, company)], notes [str])."""
    people, backed, notes = [], [], []
    for seg in (PEOPLE.get(fund) or "").split(" · "):
        t = seg.strip()
        if not t:
            continue
        if t.startswith("Backed:"):
            for item in re.findall(r"([^,(]+?)\s*\(([^)]+)\)", t[7:]):
                backed.append((item[0].strip(), item[1].strip()))
            continue
        n = t.split(",")[0].strip()
        parts = [x.strip() for x in t.split(",")]
        if not SKIP.match(t) and len(parts) > 1 and all(is_name(x) for x in parts):
            people.extend((" ".join(x.split()), "") for x in parts)
        elif not SKIP.match(t) and is_name(n):
            people.append((" ".join(n.split()), t[len(n):].lstrip(", ").strip()))
        else:
            notes.append(t)
    return people, backed, notes


def person_li(fund, name):
    for x in LEADS.get(fund, []):
        if x["n"] == name and x["li"]:
            return x["li"]
    a = norm(name)
    for x in PLI.get(fund, []):
        b = norm(x["n"])
        if len(b) >= 8 and (a.startswith(b) or b.startswith(a)):
            return x["li"]
    return None


def li_search(q, kind="people"):
    return f"https://www.linkedin.com/search/results/{kind}/?keywords=" + urllib.parse.quote(q)


def the(k):
    return "the United States" if k == "United States" else k


def stages(n):
    return [STG[s] for s in STAGE.get(n, "") if s in STG]


def lede(i):
    typ = CAT.get(i["t"], "Investor")
    where = "investing across Latin America from several regions" if i["k"] == "Global" else f"in {the(i['k'])}"
    st = stages(i["n"])
    s = f"{typ} {where}"
    if st:
        low = [x[0].lower() + x[1:] for x in st]
        s += ", backing " + (", ".join(low[:-1]) + " and " + low[-1] if len(low) > 1 else low[0]) + " rounds"
    return s + "."


css = '<link rel="stylesheet" href="../../site.css">\n<link rel="stylesheet" href="../../founders.css">\n<style>.section.tight{padding-top:40px;padding-bottom:40px}</style>'
home = lambda depth: f'<a href="{"../" * depth}../index.html">Miss Angel Investor</a>' if HOME_LINK else ""
FOOT = lambda up: f"""<footer class="footer"><div class="container"><div><p class="closing">Made by Angelica Carrillo.</p><small>Part of the Latina Founders Map: where Latina founders started, where they build today, and the investors, programs and prizes that back them.</small></div><nav aria-label="Footer"><a href="{up}">The map</a><a href="{up}investors/">All investors</a><a href="{up}founders/">All founders</a><a href="https://www.linkedin.com/in/iangie" rel="noopener">LinkedIn</a></nav></div></footer>"""


def page(i):
    n, k = i["n"], i["k"]
    typ = CAT.get(i["t"], "Investor")
    people, backed, notes = split_people(n)
    leads = LEADS.get(n, [])
    web = FWEB.get(n)
    li = FLI.get(n)
    li_url = li or li_search(n, "companies")
    url = f"{BASE}investors/{i['slug']}/"
    st = stages(n)
    terms = TERMS.get(n, {}).get("t")
    women = n in WOMEN or i["t"] == "GL"
    fl = [f for f in backed]
    for x in leads:
        m = re.match(r"(.+?) \((.+)\)", x["f"])
        if m and m.group(1) not in [f[0] for f in fl]:
            fl.append((m.group(1), m.group(2)))
    title = f"{n}: {typ}{'' if k == 'Global' else ' in ' + the(k)} | LATAM Investors Directory"
    bits = []
    if people:
        bits.append("who works there")
    if fl:
        bits.append(f"the Latina founders it backed")
    meta = f"{n} is a {typ.lower()}{' investing in Latin America' if k == 'Global' else ' in ' + the(k)}. See {', '.join(bits + ['its website and LinkedIn']) if bits else 'its website and LinkedIn'}, on the Latina Founders Map."
    ld = {"@context": "https://schema.org", "@type": "Organization", "name": n, "description": lede(i), "url": web or url,
          "mainEntityOfPage": url}
    if li:
        ld["sameAs"] = [li]
    if k not in ("Global",):
        ld["location"] = {"@type": "Place", "name": k}
    if people:
        ld["member"] = [{"@type": "Person", "name": p, **({"jobTitle": r} if r else {}), **({"sameAs": [person_li(n, p)]} if person_li(n, p) else {})} for p, r in people]
    facts = [("Type", typ + (" · women-focused" if women and i["t"] != "GL" else "")), ("Based in", "Several regions, invests in Latin America" if k == "Global" else k)]
    if st:
        facts.append(("Stages", ", ".join(st)))
    if terms:
        facts.append(("Terms", terms + " (self-reported)"))
    glance = (f"Backed {len(fl)} Latina founder{'s' if len(fl) != 1 else ''} on the map." if fl else
              f"{'Women-focused ' + typ.lower() if women else typ}, {'investing across the region' if k == 'Global' else 'based in ' + the(k)}.")
    ppl = "".join(
        f'<li><a href="{e(person_li(n, p) or li_search(p + " " + n))}" rel="noopener" target="_blank">{e(p)}</a><span>{" · ".join(x for x in [e(r), "LinkedIn profile" if person_li(n, p) else "find on LinkedIn"] if x)}</span></li>'
        for p, r in people)
    led = "".join(
        f'<li><a href="{e(x["li"] or li_search(x["n"] + " " + n))}" rel="noopener" target="_blank">{e(x["n"])}</a><span>Backed {e(x["f"])}. {e(x["r"])}. <a href="{e(x["s"])}" rel="noopener" target="_blank">Source</a></span></li>'
        for x in leads)
    fnd = "".join(
        f'<li>{f"<a href=\"../../founders/{FSLUG[f]}/\">{e(f)}</a>" if f in FSLUG else e(f)}<span>{e(c)}</span></li>' for f, c in fl)
    peers = [j for j in inv if j["k"] == k and j is not i][:10]
    body = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(meta)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:title" content="{e(n)}: {e(typ)}{'' if k == 'Global' else ' in ' + e(k)}">
<meta property="og:description" content="{e(meta)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(url)}">
{css}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<header class="nav">
 <div class="container">
  <a class="wordmark" href="../../">Latina Founders Map</a>
  <nav class="nav-links" aria-label="Main">{home(2)}<a href="../">All investors</a><a class="btn" href="../../">Open the map</a></nav>
 </div>
</header>
<main>
<section class="page-hero fp-hero">
 <div class="container">
  <div>
   <p class="eyebrow-task">{e(typ)} · {e('Global' if k == 'Global' else k)}</p>
   <h1>{e(n)}</h1>
   <p class="lead">{e(lede(i))}</p>
   <div class="actions">{f'<a class="btn" href="{e(web)}" rel="noopener" target="_blank">Visit the website</a>' if web else ''}<a class="btn{' btn-alt' if web else ''}" href="{e(li_url)}" rel="noopener" target="_blank">{'LinkedIn page' if li else 'Find on LinkedIn'}</a><a class="textlink" href="../../">See it on the map</a></div>
  </div>
  <div class="fp-brief">
   <div class="fp-short"><span>At a glance</span><p>{e(glance)}</p></div>
   <ol class="fp-notes">{"".join(f"<li>{e(a)}: {e(b)}</li>" for a, b in facts)}</ol>
  </div>
 </div>
</section>
{f'<section class="section tight"><div class="container"><h2 class="fp-h2">People at {e(n)}</h2><ul class="fp-peers">{ppl}</ul></div></section>' if ppl else ''}
{f'<section class="section tight"><div class="container"><h2 class="fp-h2">Partners who backed Latina founders</h2><ul class="fp-peers">{led}</ul></div></section>' if led else ''}
{f'<section class="section tight"><div class="container"><h2 class="fp-h2">Latina founders it backed</h2><ul class="fp-peers">{fnd}</ul></div></section>' if fnd else ''}
{f'<section class="section tight"><div class="container"><h2 class="fp-h2">Notes</h2><ul class="fp-list">{"".join(f"<li>{e(x)}</li>" for x in notes)}</ul></div></section>' if notes else ''}
<section class="section tight">
 <div class="container">
  <h2 class="fp-h2">More investors {'investing across the region' if k == 'Global' else 'in ' + e(k)}</h2>
  <ul class="fp-peers">{"".join(f'<li><a href="../{j["slug"]}/">{e(j["n"])}</a><span>{e(CAT.get(j["t"], ""))}</span></li>' for j in peers)}</ul>
  <p class="src-note">Listed from {", ".join(f'<a href="{e(u)}" rel="noopener">{e(s)}</a>' if u else e(s) for s, u in GENERAL)} and Angelica Carrillo’s research. Website and LinkedIn links are added only once verified. Work here, or see a correction? Message Angelica Carrillo on <a href="https://www.linkedin.com/in/iangie" rel="noopener">LinkedIn</a>.</p>
 </div>
</section>
</main>
{FOOT("../../")}
</body>
</html>
"""
    out = ROOT / "investors" / i["slug"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(body)


for i in inv:
    page(i)

groups = {}
for i in inv:
    groups.setdefault(i["k"], []).append(i)
order = sorted(groups, key=lambda c: (c == "Global", -len(groups[c]), c))
idx = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{len(inv)} investors backing founders in Latin America | LATAM Investors Directory</title>
<meta name="description" content="Directory of {len(inv)} VC funds, angels, accelerators, corporate VCs and prizes that invest in Latin American founders, by country, with their people, websites and the Latina founders they backed.">
<link rel="canonical" href="{BASE}investors/">
<link rel="stylesheet" href="../site.css">
<link rel="stylesheet" href="../founders.css">
<style>.inv-search{{width:100%;max-width:460px;font:inherit;padding:12px 14px;border:1px solid var(--color-line,#ccc);border-radius:10px;margin:8px 0 4px;background:transparent;color:inherit}}</style>
</head>
<body>
<header class="nav"><div class="container"><a class="wordmark" href="../">Latina Founders Map</a><nav class="nav-links" aria-label="Main">{home(1)}<a href="../founders/">All founders</a><a class="btn" href="../">Open the map</a></nav></div></header>
<main><section class="section"><div class="container">
<h1 class="fp-h1">{len(inv)} investors backing founders in Latin America</h1>
<p class="lead">VC funds, angels, accelerators, corporate VCs and prizes, grouped by where they are based. Each name opens its page, with the people there, its website and the Latina founders it backed.</p>
<label class="sr" for="q" style="position:absolute;left:-9999px">Search investors</label>
<input id="q" class="inv-search" type="search" placeholder="Search a fund, angel group or prize" autocomplete="off">
{"".join(f'<div class="ig"><h2 class="fp-h2">{e("Global players investing in LATAM" if c == "Global" else c)} · {len(groups[c])}</h2><ul class="fp-peers">' + "".join(f'<li data-n="{e(j["n"].lower())}"><a href="{j["slug"]}/">{e(j["n"])}</a><span>{e(CAT.get(j["t"], ""))}</span></li>' for j in sorted(groups[c], key=lambda j: j["n"].lower())) + "</ul></div>" for c in order)}
</div></section></main>
{FOOT("../")}
<script>document.getElementById("q").addEventListener("input",function(){{var q=this.value.trim().toLowerCase();document.querySelectorAll(".ig").forEach(function(g){{var any=0;g.querySelectorAll("li").forEach(function(li){{var ok=!q||li.dataset.n.indexOf(q)>-1;li.style.display=ok?"":"none";any+=ok}});g.style.display=any?"":"none"}})}});</script>
</body></html>
"""
(ROOT / "investors" / "index.html").write_text(idx)

sm = ROOT / "sitemap.xml"
s = sm.read_text() if sm.exists() else '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n</urlset>\n'
s = re.sub(r"  <url><loc>[^<]*/investors/[^<]*</loc>.*?</url>\n", "", s)
add = [f"{BASE}investors/"] + [f"{BASE}investors/{i['slug']}/" for i in inv]
s = s.replace("</urlset>", "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in add) + "</urlset>")
sm.write_text(s)
(ROOT / "investors-slugs.js").write_text("// generated by build_investors.py: investor name -> page slug\nwindow.ISLUG=" + json.dumps(ISLUG, ensure_ascii=False) + ";\n")
print(len(inv), "investor pages,", sum(1 for i in inv if FWEB.get(i["n"])), "with website,", sum(1 for i in inv if FLI.get(i["n"])), "with verified LinkedIn")
