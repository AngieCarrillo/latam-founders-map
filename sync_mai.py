"""Copy the public map into the Miss Angel Investor site at /map/.

Run from this folder after any map change:  python3 -I sync_mai.py
Then commit + push the MAI repo (~/Downloads/projects/MissAngelInvestor/site/v3); Vercel deploys it.
Founder pages are rebuilt with canonical URLs on missangelinvestor.com/map/.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
MAI = Path.home() / "Downloads/projects/MissAngelInvestor/site/v3"
DST = MAI / "map"
BASE = "https://missangelinvestor.com/map/"

if DST.exists():
    shutil.rmtree(DST)
DST.mkdir(parents=True)
for f in ["index.html", "base.css", "site.css", "tokens.css", "founders.css", "founders.js",
          "founders-data.js", "invglobe.js", "founders-linkedin.json", "founders-websites.json",
          "fund-linkedin.json", "fund-websites.json", "people-linkedin.json", "investors-slugs.js"]:
    shutil.copy2(SRC / f, DST / f)
shutil.copytree(SRC / "fonts", DST / "fonts")

# rebuild founder pages, sitemap and slugs inside the copy, with the MAI base URL
code = (SRC / "build_pages.py").read_text()
code = re.sub(r'^BASE = .*$', f'BASE = "{BASE}"', code, count=1, flags=re.M)
code = code.replace("ROOT = Path(__file__).resolve().parent", f"ROOT = Path({str(DST)!r})")
code = code.replace("Latina Founders Map</a>\n  <nav class=\"nav-links\" aria-label=\"Main\">",
                    "Latina Founders Map</a>\n  <nav class=\"nav-links\" aria-label=\"Main\"><a href=\"../../../index.html\">Miss Angel Investor</a>")
exec(compile(code, "build_pages.py", "exec"), {"__name__": "__main__"})
code = (SRC / "build_investors.py").read_text()
code = re.sub(r'^BASE = .*$', f'BASE = "{BASE}"', code, count=1, flags=re.M)
code = code.replace("ROOT = Path(__file__).resolve().parent", f"ROOT = Path({str(DST)!r})")
code = code.replace('HOME_LINK = ""', 'HOME_LINK = "yes"')
exec(compile(code, "build_investors.py", "exec"), {"__name__": "__main__"})

# map header: link back to the MAI home
p = DST / "index.html"
s = p.read_text()
s = s.replace('<a class="wordmark" href="./">Angelica Carrillo</a>',
              '<a class="wordmark" href="../index.html">Angie Carrillo</a>', 1)
s = s.replace('<nav class="nav-links" aria-label="Main">',
              '<nav class="nav-links" aria-label="Main">\n   <a href="../index.html">Miss Angel Investor</a>', 1)
if "<link rel=\"canonical\"" not in s:
    s = s.replace("</title>", f"</title>\n<link rel=\"canonical\" href=\"{BASE}\">", 1)
p.write_text(s)

for f in ["founders-linkedin.json", "founders-websites.json", "fund-linkedin.json", "fund-websites.json", "people-linkedin.json", "robots.txt"]:
    (DST / f).unlink(missing_ok=True)

# Miss Angel Investor branding: load mai-theme.css last on every page
shutil.copy2(SRC / "mai-theme.css", DST / "mai-theme.css")
for h in DST.rglob("*.html"):
    rel = "../" * (len(h.relative_to(DST).parts) - 1)
    t = h.read_text()
    if "mai-theme.css" not in t:
        h.write_text(t.replace("</head>", f'<link rel="stylesheet" href="{rel}mai-theme.css">\n</head>', 1))

# root robots.txt points at the map sitemap
(MAI / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
print("synced to", DST)
