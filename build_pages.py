"""Build one SEO page per founder, a founders index, sitemap.xml and robots.txt.

Run from this folder:  python3 -I build_pages.py
Reads founders-data.js (FW, FC), founders-linkedin.json and index.html (PEOPLE, for "Backed:").
Change BASE when the map moves to its own domain (e.g. https://map.iangie.com/).
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

data = (ROOT / "founders-data.js").read_text()
FW = json.loads(re.search(r"window\.FW=(\[.*?\]);\n", data).group(1))
FC = json.loads(re.search(r"window\.FC=(\{.*?\});\n", data).group(1))
LI = json.loads((ROOT / "founders-linkedin.json").read_text())
WEB = json.loads((ROOT / "founders-websites.json").read_text()) if (ROOT / "founders-websites.json").exists() else {}
INDEX = (ROOT / "index.html").read_text()
PEOPLE = json.loads(re.search(r"const PEOPLE=(\{.*?\});", INDEX).group(1))

SOURCES = {
    1: ("Startupeable’s Diaspora map", "https://www.startupeable.com/diaspora/"),
    2: ("Aurora’s Top 30 Women Founders to Watch in LatAm", "https://www.auroratechaward.com/top-30-women-founders-latam"),
    3: ("Angelica Carrillo’s network and research", None),
    6: ("Y Combinator’s Latin America companies", "https://www.ycombinator.com/companies?regions=Latin%20America"),
    5: ("Harlem Capital and Crunchbase’s 2022 Black & Latino Founder Report", "https://airtable.com/appTolMiRbOFudS3O/shrkMKANni00yoPru/tblRVApDjCyG3m028"),
}
e = lambda s: html.escape(str(s), quote=True)


def slugify(name):
    s = unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def flag(a2):
    return "".join(chr(127397 + ord(c)) for c in a2.upper())


def cname(cid):
    return FC[cid][0]


def company_of(r):
    co = r[3]
    if r[1] == 2:  # Aurora: "Company · Sector · Stage"
        return co.split(" · ")[0]
    if r[1] == 1 and "," in co:  # wishlist roles: "Co-founder, Nubank"
        return co.split(",")[-1].strip()
    return co


# investors on the map that backed each founder
backers = {}
for firm, note in PEOPLE.items():
    m = re.search(r"Backed: ([^·]+)", note)
    if not m:
        continue
    for item in m.group(1).split(","):
        backers.setdefault(item.split(" (")[0].strip(), []).append(firm)

founders, used = [], set()
for r in FW:
    slug = slugify(r[0])
    while slug in used:
        slug += "-2"
    used.add(slug)
    founders.append({"r": r, "slug": slug})

def first_sentence(t):
    m = re.match(r"(.+?[.!?])(\s|$)", t)
    return (m.group(1) if m else t).strip()


def brief(r, company):
    """In short + up to 3 notes, built only from data we hold."""
    name, src, o, dp, city, desc = r[0], r[1], r[2], r[4], r[5], (r[8] if len(r) > 8 else "") or ""
    builds = city if src == 2 else (f"{city}, {cname(dp)}" if city != cname(dp) else cname(dp))
    parts = [x.strip() for x in r[3].split(" · ")] if src == 2 else []
    notes = []
    if src == 5:  # "Sector · $X raised · Stage"
        bits = [b.strip() for b in desc.split(" · ") if b.strip()]
        sector = bits[0] if bits else ""
        short = f"Founder of {company}, a {sector.lower()} company in {city}." if sector else f"Founder of {company}, building in {city}."
        if len(bits) > 1:
            notes.append(f"{company} has raised {bits[1].replace(' raised','')}" + (f", latest round {bits[2]}." if len(bits) > 2 else "."))
    elif desc:
        short = first_sentence(desc)
        rest = desc[len(short):].strip()
        if rest:
            notes.append(rest)
    else:
        short = f"Founder of {company}, building in {builds}."
    if src == 2 and len(parts) >= 3:
        notes.append(f"{parts[1]} company at {parts[2].lower()} stage, picked for Aurora’s Top 30 Women Founders to Watch in LatAm.")
    if o != dp:
        notes.append(f"Started in {cname(o)}, builds in {builds} today.")
    else:
        notes.append(f"Started and builds in {builds if src != 2 else cname(dp)}.")
    inv = backers.get(name, [])
    if inv:
        more = f" and {len(inv) - 3} more" if len(inv) > 3 else ""
        notes.append(f"Backed by {', '.join(inv[:3])}{more} on the investor map.")
    return short, notes[:3]


css = '<link rel="stylesheet" href="../../site.css">\n<link rel="stylesheet" href="../../founders.css">'


def page(f):
    r = f["r"]
    name, src, o, dp, city = r[0], r[1], r[2], r[4], r[5]
    company = company_of(r)
    desc_extra = r[8] if len(r) > 8 and r[8] else ""
    short, notes = brief(r, company)
    started = f"{flag(FC[o][1])} {cname(o)}"
    builds = city if src == 2 else (f"{city}, {cname(dp)}" if city not in (cname(dp),) else cname(dp))
    moved = o != dp
    li = LI.get(name)
    li_url = li or "https://www.linkedin.com/search/results/people/?keywords=" + urllib.parse.quote(f"{name} {company}")
    li_label = "View her LinkedIn profile" if li else "Find her on LinkedIn"
    title = f"{name}, founder of {company} | Latina Founders Map"
    route = f"from {cname(o)}, building in {builds}" if moved else f"building in {builds}"
    meta = f"{name}, founder of {company}: {short} See her investors and more Latina founders on the Latina Founders Map."
    url = f"{BASE}founders/{f['slug']}/"
    peers = [g for g in founders if g is not f and g["r"][2] == o][:8]
    inv = backers.get(name, [])
    sname, slink = SOURCES.get(src, ("", None))
    ld = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": name,
        "jobTitle": "Founder",
        "worksFor": {"@type": "Organization", "name": company},
        "homeLocation": {"@type": "Place", "name": builds},
        "url": url,
    }
    if li:
        ld["sameAs"] = [li]
    site = WEB.get(name)
    crunch = r[7] if "crunchbase.com/organization/" in r[7] else None
    if crunch:
        ld["worksFor"]["sameAs"] = [crunch]
    if site:
        ld["worksFor"]["url"] = site
    body = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(meta)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:title" content="{e(name)}, founder of {e(company)}">
<meta property="og:description" content="{e(meta)}">
<meta property="og:type" content="profile">
<meta property="og:url" content="{e(url)}">
{css}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<header class="nav">
 <div class="container">
  <a class="wordmark" href="../../">Latina Founders Map</a>
  <nav class="nav-links" aria-label="Main"><a href="../">All founders</a><a class="btn" href="../../">Open the map</a></nav>
 </div>
</header>
<main>
<section class="page-hero fp-hero">
 <div class="container">
  <div>
   <p class="eyebrow-task">Founder profile</p>
   <h1>{e(name)}</h1>
   <p class="lead">Founder of <b>{e(company)}</b>, {e(route)}.</p>
   <div class="actions"><a class="btn" href="{e(li_url)}" rel="noopener" target="_blank">{li_label}</a>{f'<a class="btn btn-alt" href="{e(site)}" rel="noopener" target="_blank">Visit {e(company)}</a>' if site else ''}{f'<a class="btn btn-alt" href="{e(crunch)}" rel="noopener" target="_blank">{e(company)} on Crunchbase</a>' if crunch else ''}<a class="textlink" href="../../#founders">See her on the map</a></div>
  </div>
  <div class="fp-brief">
   <div class="fp-short"><span>In short</span><p>{e(short)}</p></div>
   <ol class="fp-notes">{"".join(f"<li>{e(n)}</li>" for n in notes)}</ol>
  </div>
 </div>
</section>
{f'''<section class="section tight"><div class="container"><h2 class="fp-h2">Investors on the map who backed her</h2><ul class="fp-list">{"".join(f"<li>{e(i)}</li>" for i in inv)}</ul></div></section>''' if inv else ''}
<section class="section tight">
 <div class="container">
  <h2 class="fp-h2">More Latina founders from {e(cname(o))}</h2>
  <ul class="fp-peers">{"".join(f'<li><a href="../{g["slug"]}/">{e(g["r"][0])}</a><span>{e(company_of(g["r"]))}</span></li>' for g in peers)}</ul>
  <p class="src-note">Listed from {f'<a href="{e(slink)}" rel="noopener">{e(sname)}</a>' if slink else e(sname)}. Corrections or a better LinkedIn link? Message Angelica Carrillo on <a href="https://www.linkedin.com/in/iangie" rel="noopener">LinkedIn</a>.</p>
 </div>
</section>
</main>
<footer class="footer"><div class="container"><div><p class="closing">Made by Angelica Carrillo.</p><small>Part of the Latina Founders Map: where Latina founders started, where they build today, and the investors, programs and prizes that back them.</small></div><nav aria-label="Footer"><a href="../../">The map</a><a href="../">All founders</a><a href="https://www.linkedin.com/in/iangie" rel="noopener">LinkedIn</a></nav></div></footer>
</body>
</html>
"""
    out = ROOT / "founders" / f["slug"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(body)


for f in founders:
    page(f)

# founders index, grouped by where she started
groups = {}
for f in founders:
    groups.setdefault(f["r"][2], []).append(f)
order = sorted(groups, key=lambda c: (-len(groups[c]), cname(c)))
idx = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>All {len(founders)} Latina founders | Latina Founders Map</title>
<meta name="description" content="Directory of {len(founders)} Latina founders by country: where they started, where they build today and who backed them.">
<link rel="canonical" href="{BASE}founders/">
<link rel="stylesheet" href="../site.css">
<link rel="stylesheet" href="../founders.css">
</head>
<body>
<header class="nav"><div class="container"><a class="wordmark" href="../">Latina Founders Map</a><nav class="nav-links" aria-label="Main"><a class="btn" href="../">Open the map</a></nav></div></header>
<main><section class="section"><div class="container">
<h1 class="fp-h1">All {len(founders)} Latina founders</h1>
<p class="lead">Grouped by where she started. Each name opens her page.</p>
{"".join(f'<h2 class="fp-h2">{flag(FC[c][1])} {e(cname(c))} · {len(groups[c])}</h2><ul class="fp-peers">' + "".join(f'<li><a href="{g["slug"]}/">{e(g["r"][0])}</a><span>{e(company_of(g["r"]))}</span></li>' for g in sorted(groups[c], key=lambda g: g["r"][0])) + "</ul>" for c in order)}
</div></section></main>
<footer class="footer"><div class="container"><div><p class="closing">Made by Angelica Carrillo.</p></div><nav aria-label="Footer"><a href="../">The map</a><a href="https://www.linkedin.com/in/iangie" rel="noopener">LinkedIn</a></nav></div></footer>
</body></html>
"""
(ROOT / "founders" / "index.html").write_text(idx)

urls = [BASE, f"{BASE}founders/"] + [f"{BASE}founders/{f['slug']}/" for f in founders]
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)
    + "</urlset>\n"
)
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
(ROOT / "founders-slugs.js").write_text("// generated by build_pages.py: founder name -> profile page slug\nwindow.FSLUG=" + json.dumps({f["r"][0]: f["slug"] for f in founders}, ensure_ascii=False) + ";\n")
print(len(founders), "founder pages,", len(urls), "sitemap URLs")
