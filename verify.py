#!/usr/bin/env python3
"""Checks dist/ against SPEC.md acceptance criteria. Exit 0 = no FAIL."""
import json
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
sys.path.insert(0, ROOT)
import config  # noqa: E402

P = json.load(open(os.path.join(ROOT, "data", "paper.json"), encoding="utf-8"))
SITE = config.site_url(sys.argv, P)
THEME = config.theme(sys.argv, P)
DOI = P["doi"]
DOI_URL = f"https://doi.org/{DOI}"

results = []  # (id, status, message)


def rec(ac, ok, msg, warn=False):
    results.append((ac, "PASS" if ok else ("WARN" if warn else "FAIL"), msg))


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.metas, self.links, self.imgs, self.hrefs = [], [], [], [], []
        self.headings, self.ld, self.scripts, self.title = [], [], [], ""
        self._in_title = self._in_h = self._in_ld = False
        self._buf = ""
        self.html_attrs = {}
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "html":
            self.html_attrs = a
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            self.metas.append(a)
        elif tag == "link":
            self.links.append(a)
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "a" and a.get("href") is not None:
            self.hrefs.append(a["href"])
        elif tag == "script":
            if a.get("type") == "application/ld+json":
                self._in_ld = True
                self._buf = ""
            else:
                self.scripts.append(a)
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append(int(tag[1]))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_ld:
            self._in_ld = False
            self.ld.append(self._buf)

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_ld:
            self._buf += data

    def meta(self, key):
        return [m.get("content", "") for m in self.metas if m.get("name") == key or m.get("property") == key]


def load(rel):
    raw = open(os.path.join(DIST, rel), encoding="utf-8").read()
    p = Page()
    p.feed(raw)
    return p, raw


PAGES = {"": "index.html", "cite/": "cite/index.html",
         "background/pseudocode-to-python/": "background/pseudocode-to-python/index.html"}
ALL = dict(PAGES, **{"404.html": "404.html"})
parsed = {k: load(v) for k, v in ALL.items()}

# AC-01 / AC-02
bad = [k for k in PAGES if parsed[k][0].headings.count(1) != 1]
rec("AC-01", not bad, "one <h1> per indexable page" if not bad else f"pages with !=1 h1: {bad}")
h1_home = re.search(r"<h1>(.*?)</h1>", parsed[""][1], re.S).group(1)
import html as _h
rec("AC-02", _h.unescape(h1_home) == P["title"], "home H1 equals paper.title")

# AC-03 titles
titles = {k: parsed[k][0].title.strip() for k in PAGES}
bad = [k for k, t in titles.items() if not (20 <= len(t) <= (90 if k == "" else 65))]
dup = len(set(titles.values())) != len(titles)
rec("AC-03", not bad and not dup, f"title lengths {[len(t) for t in titles.values()]}, unique={not dup}")

# AC-04 descriptions
descs = {k: (parsed[k][0].meta("description") or [""])[0] for k in PAGES}
bad = [k for k, d in descs.items() if not (70 <= len(d) <= 160)]
dup = len(set(descs.values())) != len(descs)
rec("AC-04", not bad and not dup, f"description lengths {[len(d) for d in descs.values()]}, unique={not dup}")

# AC-05 canonical
bad = []
for k in PAGES:
    c = [l.get("href") for l in parsed[k][0].links if l.get("rel") == "canonical"]
    if c != [f"{SITE}/{k}"]:
        bad.append((k, c))
rec("AC-05", not bad, "self-referencing canonicals" if not bad else str(bad))

# AC-06
bad = [k for k in ALL if parsed[k][0].html_attrs.get("lang") != "en" or not parsed[k][0].meta("viewport")]
rec("AC-06", not bad, "lang=en + viewport on all pages" if not bad else str(bad))

# AC-07
need = ["og:title", "og:description", "og:type", "og:url", "og:image", "twitter:card"]
bad = [(k, n) for k in PAGES for n in need if not parsed[k][0].meta(n)]
rec("AC-07", not bad, "Open Graph + Twitter tags present" if not bad else str(bad))

# AC-08
bad = []
for k in PAGES:
    prev = 0
    for h in parsed[k][0].headings:
        if prev and h > prev + 1:
            bad.append(k)
        prev = h
rec("AC-08", not bad, "no skipped heading levels" if not bad else str(bad))

# AC-09
bad = [k for k in ALL for i in parsed[k][0].imgs if not i.get("alt", "").strip()]
rec("AC-09", not bad, f"{sum(len(parsed[k][0].imgs) for k in ALL)} <img> tags, all with alt")

# AC-10
home = parsed[""][0]
need = ["citation_title", "citation_author", "citation_publication_date", "citation_doi", "citation_publisher"]
miss = [n for n in need if not home.meta(n)]
nauth = len(home.meta("citation_author"))
ok = not miss and nauth == len(P["authors"]) and home.meta("citation_doi") == [DOI]
if bool(P.get("pdf_url")) != bool(home.meta("citation_pdf_url")):
    ok = False
rec("AC-10", ok, f"Highwire tags ok ({nauth} author tag(s))" if ok else f"missing {miss}")

# AC-11
need = ["DC.title", "DC.creator", "DC.date", "DC.identifier", "DC.publisher"]
miss = [n for n in need if not home.meta(n)]
rec("AC-11", not miss and home.meta("DC.identifier") == [DOI_URL], "Dublin Core tags ok" if not miss else f"missing {miss}")


def ld_objects(p):
    out, err = [], 0
    for raw in p.ld:
        try:
            out.append(json.loads(raw))
        except Exception:
            err += 1
    return out, err


# AC-14 first, since later checks depend on parsing
errs = {k: ld_objects(parsed[k][0])[1] for k in ALL}
rec("AC-14", not any(errs.values()), "all JSON-LD parses" if not any(errs.values()) else str(errs))

# AC-12
objs, _ = ld_objects(home)
graph = [n for o in objs for n in (o.get("@graph") or [o])]
art = next((n for n in graph if n.get("@type") == "ScholarlyArticle"), {})
req = ["name", "author", "datePublished", "identifier", "url", "sameAs", "publisher", "inLanguage"]
miss = [r for r in req if not art.get(r)]
ok = (not miss and art.get("sameAs") == DOI_URL and art["identifier"].get("propertyID") == "DOI"
      and art["identifier"].get("value") == DOI)
if P.get("keywords") and not art.get("keywords"):
    ok = False
if not P.get("keywords") and art.get("keywords"):
    ok = False
rec("AC-12", ok, "ScholarlyArticle JSON-LD complete" if ok else f"missing/invalid {miss}")

# AC-13
okb = True
for k in ("cite/", "background/pseudocode-to-python/"):
    o, _ = ld_objects(parsed[k][0])
    if not any(x.get("@type") == "BreadcrumbList" for x in o):
        okb = False
o, _ = ld_objects(parsed["background/pseudocode-to-python/"][0])
if not any(x.get("@type") == "Article" for x in o):
    okb = False
rec("AC-13", okb, "BreadcrumbList on subpages, Article on background")

# AC-15
sm = open(os.path.join(DIST, "sitemap.xml"), encoding="utf-8").read()
locs = re.findall(r"<loc>(.*?)</loc>", sm)
exp = [f"{SITE}/{k}" for k in PAGES]
ok = sorted(locs) == sorted(exp) and sm.count("<lastmod>") == len(exp) and "404" not in sm
rec("AC-15", ok, f"sitemap lists {len(locs)} URLs with lastmod" if ok else f"{locs} vs {exp}")

# AC-16
rb = open(os.path.join(DIST, "robots.txt"), encoding="utf-8").read()
ok = "Allow: /" in rb and f"Sitemap: {SITE}/sitemap.xml" in rb and "Disallow: /" not in rb.replace("Disallow: /\n", "X") or ("Disallow" not in rb)
rec("AC-16", "Allow: /" in rb and f"Sitemap: {SITE}/sitemap.xml" in rb and "Disallow" not in rb, "robots.txt allows all + sitemap")

# AC-17
rec("AC-17", any("noindex" in c for c in parsed["404.html"][0].meta("robots")), "404 has noindex")

# AC-18 / AC-19 internal links
files = set()
for dp, _, fs in os.walk(DIST):
    for f in fs:
        files.add(os.path.relpath(os.path.join(dp, f), DIST).replace(os.sep, "/"))


def resolve(from_key, href):
    if href.startswith(("http://", "https://", "mailto:", "#")):
        return None
    base = "/".join(ALL[from_key].split("/")[:-1])
    if href.startswith("/"):
        target = href.lstrip("/")
    else:
        parts = [s for s in (base + "/" + href).split("/") if s]
        stack = []
        for s in parts:
            if s == "..":
                stack and stack.pop()
            elif s != ".":
                stack.append(s)
        target = "/".join(stack)
        if href.endswith("/") and not target.endswith("/"):
            target += "/"
    target = target.split("#")[0].lstrip("/")
    if target == "" or target.endswith("/"):
        target += "index.html"
    return target


broken, graph_edges = [], {k: set() for k in PAGES}
rev = {v: k for k, v in PAGES.items()}
for k in ALL:
    for h in parsed[k][0].hrefs:
        t = resolve(k, h)
        if t is None:
            continue
        if t not in files:
            broken.append((k, h))
        elif k in graph_edges and t in rev:
            graph_edges[k].add(rev[t])
rec("AC-18", not broken, "all internal links resolve" if not broken else str(broken))
seen, frontier = {""}, {""}
for _ in range(2):
    frontier = {n for f in frontier for n in graph_edges[f]} - seen
    seen |= frontier
rec("AC-19", seen == set(PAGES), f"{len(seen)}/{len(PAGES)} pages within 2 clicks of home")

# AC-20 / 21 / 22
ext = []
for k in ALL:
    p, raw = parsed[k]
    for l in p.links:
        h = l.get("href", "")
        if h.startswith("http") and l.get("rel") not in ("canonical",):
            ext.append((k, h))
    if re.search(r'<(script|img|iframe|link)[^>]+(src|href)="https?://', raw) and any(
        re.search(r'<(script|img|iframe)[^>]+src="https?://', raw) for _ in [0]):
        ext.append((k, "external src"))
    if "@import" in raw or "url(http" in raw:
        ext.append((k, "css external"))
rec("AC-20", not ext, "no external requests" if not ext else str(ext))
rec("AC-21", not any(parsed[k][0].scripts for k in ALL) and not any("<script" in parsed[k][1].replace('type="application/ld+json"', "") .split("<script type")[0] for k in []),
    "no JavaScript (only JSON-LD data blocks)")
big = {k: os.path.getsize(os.path.join(DIST, v)) for k, v in ALL.items() if os.path.getsize(os.path.join(DIST, v)) > 60 * 1024}
rec("AC-22", not big, "all HTML <= 60 KB" if not big else str(big))

# AC-23
bad = []
for k in PAGES:
    p, raw = parsed[k]
    if not all(t in p.tags for t in ("header", "nav", "main", "footer")) or 'class="skip"' not in raw or ":focus-visible" not in raw:
        bad.append(k)
rec("AC-23", not bad, "skip link, landmarks, focus styles" if not bad else str(bad))


# AC-24 contrast
def lum(hexc):
    hexc = hexc.lstrip("#")
    if len(hexc) == 3:
        hexc = "".join(c * 2 for c in hexc)
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


css = re.search(r"<style>(.*?)</style>", parsed[""][1], re.S).group(1)
HEX = r"--([\w-]+):(#[0-9a-fA-F]{3,6})"
base = dict(re.findall(HEX, css.split("@media")[0]))
alt_block = css.split("@media (prefers-color-scheme:", 1)[1].split("}}")[0]
alt = {**base, **dict(re.findall(HEX, alt_block))}
schemes = {"scheme-1 (base)": base, "scheme-2 (prefers-color-scheme override)": alt}
pairs = [("text", "bg"), ("muted", "bg"), ("link", "bg"), ("muted", "card"), ("link", "card"), ("text", "card"), ("btn-text", "btn")]
if THEME == "cs":
    pairs += [("accent", "bg"), ("accent", "card"), ("muted", "code")]
low = []
for name, theme in schemes.items():
    for a, b in pairs:
        r = ratio(theme[a], theme[b])
        if r < 4.5:
            low.append((name, a, b, round(r, 2)))
rec("AC-24", not low, "contrast >= 4.5:1 in both colour schemes" if not low else str(low))

# AC-25
ok = all(parsed[k][0].meta("viewport") for k in ALL) and "overflow-wrap:anywhere" in css and re.search(r"\.wrap\{max-width:\d+rem", css)
rec("AC-25", ok, "fluid layout, wrapping long strings, viewport set (320px-safe)")

# AC-26
ok = True
for k in ("", "cite/"):
    raw = parsed[k][1]
    if DOI not in raw:
        ok = False
for k in ALL:
    for h in parsed[k][0].hrefs:
        if "doi.org/" in h and h.startswith("https://doi.org/10.5281") and h != DOI_URL:
            ok = False
rec("AC-26", ok, "DOI present on home + cite; all Zenodo DOI links correct")

# AC-27 / AC-28 warnings
rec("AC-27", "YOUR-DOMAIN" not in SITE and "example" not in urlparse(SITE).netloc,
    f"site_url = {SITE}" + ("" if "YOUR-DOMAIN" not in SITE else "  (placeholder: set before deploy)"), warn=True)
missing = [f for f in ("abstract", "keywords", "pdf_url", "license_name") if not P.get(f)]
if P.get("authors_incomplete"):
    missing.append("full author list (authors_incomplete=true)")
rec("AC-28", not missing, "no optional fields missing" if not missing else "not supplied, omitted from output: " + ", ".join(missing), warn=True)

# ---------------------------------------------------------------- v1.1 checks
home_raw = parsed[""][1]
NA = f"n/a for theme '{THEME}'"

# AC-29 / AC-31 / AC-33 (cs theme only)
if THEME == "cs":
    ok = ("--mono:" in css and "color-scheme:dark light" in css and "@media (prefers-color-scheme:light)" in css
          and re.search(r"h1\{font:[^}]*var\(--mono\)", css))
    rec("AC-29", bool(ok), "mono stack, dark default, light scheme via prefers-color-scheme")
    syn = [("kw", "code"), ("str", "code"), ("cm", "code"), ("num", "code"), ("fn", "code"), ("text", "code")]
    lowsyn = [(n, a, round(ratio(t[a], t[b]), 2)) for n, t in schemes.items() for a, b in syn if ratio(t[a], t[b]) < 4.5]
    rec("AC-31", not lowsyn, "syntax colours >= 4.5:1 on code background in both schemes" if not lowsyn else str(lowsyn))
    ok = ("content:counter(ln)" in css and "user-select:none" in css
          and 'class="ln"' not in home_raw and not re.search(r'<span class="l">\s*\d+\s', home_raw))
    rec("AC-33", ok, "line numbers are CSS-generated and unselectable")
else:
    for ac in ("AC-29", "AC-31", "AC-33"):
        rec(ac, True, NA)

# AC-30 hero figure
if THEME == "cs":
    fig = re.search(r'<figure class="hero-code">(.*?)</figure>', home_raw, re.S)
    ok = bool(fig) and "Illustration" in fig.group(1) and "not output from the paper" in fig.group(1) \
        and len(re.findall(r"<pre[^>]*><code", fig.group(1))) == 2 and "<figcaption>" in fig.group(1)
    rec("AC-30", ok, "hero figure: 2 code panes + illustration caption")
else:
    rec("AC-30", True, NA)

# AC-32 every <pre> focusable
tabless = [(k, t) for k in ALL for t in re.findall(r"<pre\b[^>]*>", parsed[k][1]) if 'tabindex="0"' not in t]
rec("AC-32", not tabless, "every <pre> has tabindex=0" if not tabless else str(tabless))

# AC-34 / AC-35 vercel.json
try:
    vj = json.load(open(os.path.join(ROOT, "vercel.json"), encoding="utf-8"))
    ok = (vj.get("outputDirectory") == "dist" and vj.get("buildCommand") and vj.get("cleanUrls") is True
          and vj.get("trailingSlash") is True)
    rec("AC-34", bool(ok), "vercel.json: outputDirectory, buildCommand, cleanUrls, trailingSlash")
except Exception as e:  # noqa: BLE001
    vj = {}
    rec("AC-34", False, f"vercel.json unreadable: {e}")
hdrs = {h["key"]: h["value"] for blk in vj.get("headers", []) if blk.get("source") == "/(.*)" for h in blk["headers"]}
csp = hdrs.get("Content-Security-Policy", "")
need = ["X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy", "Content-Security-Policy"]
ok = (all(n in hdrs for n in need) and "default-src 'none'" in csp and "frame-ancestors 'none'" in csp
      and "script-src" not in csp and "unsafe-eval" not in csp and "http" not in csp)
rec("AC-35", ok, "security headers + strict CSP on all routes" if ok else f"missing/weak: {[n for n in need if n not in hdrs]} csp={csp!r}")

# AC-36 site URL resolution order
saved = {k: os.environ.pop(k, None) for k in ("SITE_URL", "VERCEL_PROJECT_PRODUCTION_URL")}
try:
    ph = {"site_url": "https://YOUR-DOMAIN.example"}
    real = {"site_url": "https://paper.example.org"}
    t = []
    t.append(config.site_url(["--site-url", "https://flag.test"], real) == "https://flag.test")
    os.environ["SITE_URL"] = "env.test"
    t.append(config.site_url([], real) == "https://env.test")
    del os.environ["SITE_URL"]
    t.append(config.site_url([], real) == "https://paper.example.org")
    os.environ["VERCEL_PROJECT_PRODUCTION_URL"] = "proj.vercel.app"
    t.append(config.site_url([], ph) == "https://proj.vercel.app")
    del os.environ["VERCEL_PROJECT_PRODUCTION_URL"]
    try:
        config.check_production(["--production"], config.site_url([], ph))
        t.append(False)
    except SystemExit:
        t.append(True)
finally:
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v
rec("AC-36", all(t), "site URL order flag > SITE_URL > paper.json > Vercel var; placeholder fails in --production" if all(t) else f"results {t}")

# AC-38 links compatible with cleanUrls + trailingSlash
badl = []
for k in PAGES:
    for h in parsed[k][0].hrefs:
        if h.startswith(("http", "mailto:", "#")):
            continue
        if h.endswith(".html") or "index.html" in h:
            badl.append((k, h))
        elif not h.endswith("/") and not re.search(r"\.(svg|bib|ris|png|txt|xml)$", h):
            badl.append((k, h))
rec("AC-38", not badl, "internal links use trailing slashes / real file names" if not badl else str(badl))

# AC-37 last, because it rebuilds dist without Pillow
import struct
import subprocess
asset = os.path.join(ROOT, "assets", "og-image.png")
ok = os.path.exists(asset)
if ok:
    hdr = open(asset, "rb").read(24)
    ok = hdr[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", hdr[16:24]) == (1200, 630)
if ok:
    passthru = [a for a in sys.argv[1:]]
    code = ("import sys,runpy; sys.modules['PIL']=None; sys.argv=['build.py']+%r; runpy.run_path('build.py', run_name='__main__')" % passthru)
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    ok = r.returncode == 0 and open(os.path.join(DIST, "og-image.png"), "rb").read() == open(asset, "rb").read()
rec("AC-37", ok, "assets/og-image.png is 1200x630 and the build succeeds without Pillow")

# report
w = max(len(r[2]) for r in results)
fails = 0
for ac, st, msg in results:
    print(f"{st:4}  {ac}  {msg}")
    fails += st == "FAIL"
print(f"\n{sum(r[1]=='PASS' for r in results)} pass, {sum(r[1]=='WARN' for r in results)} warn, {fails} fail")
sys.exit(1 if fails else 0)
