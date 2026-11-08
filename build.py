#!/usr/bin/env python3
"""Static site generator for the paper website. Implements SPEC.md.

Usage:  python3 build.py [--site-url https://your-domain.tld] [--theme cs|classic] [--production]
Reads:  data/paper.json
Writes: dist/
Stdlib only, except Pillow (optional) for the social preview image.
"""
import glob
import html
import json
import os
import re
import shutil
import sys
import textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")

sys.path.insert(0, ROOT)
import config  # noqa: E402

P = json.load(open(os.path.join(ROOT, "data", "paper.json"), encoding="utf-8"))
SITE = config.site_url(sys.argv, P)
THEME = config.theme(sys.argv, P)
config.check_production(sys.argv, SITE)
DOI = P["doi"]
DOI_URL = f"https://doi.org/{DOI}"
MODIFIED = P.get("date_modified", P["date_published"])

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MLA_MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July", "Aug.",
              "Sept.", "Oct.", "Nov.", "Dec."]
IEEE_MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.",
               "Sep.", "Oct.", "Nov.", "Dec."]
Y, M, D = (int(x) for x in P["date_published"].split("-"))


def esc(s):
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- authors
def authors_inverted():
    """Family, Initials list, with et al. if incomplete."""
    names = [f'{a["family"]}, {a["initials"]}' for a in P["authors"]]
    s = ", ".join(names)
    return s + (", et al." if P.get("authors_incomplete") else "")


def authors_natural():
    names = [f'{a["initials"]} {a["family"]}' for a in P["authors"]]
    s = ", ".join(names)
    return s + (" et al." if P.get("authors_incomplete") else "")


def authors_bibtex():
    names = [f'{a["family"]}, {a["initials"]}' for a in P["authors"]]
    if P.get("authors_incomplete"):
        names.append("others")
    return " and ".join(names)


# --------------------------------------------------------------- citations
T = P["title"]
CITES = {
    "APA": f"{authors_inverted()} ({Y}). {T}. {P['publisher']}. {DOI_URL}",
    "MLA": f"{authors_inverted()} “{T}.” {P['publisher']}, {D} {MLA_MONTHS[M-1]} {Y}, {DOI_URL}.",
    "Chicago": f"{authors_inverted()} {Y}. “{T}.” {P['publisher']}, {MONTHS[M-1]} {D}. {DOI_URL}.",
    "IEEE": f"{authors_natural()}, “{T},” {P['publisher']}, {IEEE_MONTHS[M-1]} {D}, {Y}, doi: {DOI}.",
}
BIBKEY = f'{P["authors"][0]["family"].lower()}{Y}pseudocode'
BIBTEX = (
    f"@misc{{{BIBKEY},\n"
    f"  author    = {{{authors_bibtex()}}},\n"
    f"  title     = {{{T}}},\n"
    f"  year      = {{{Y}}},\n"
    f"  month     = {{{MONTHS[M-1][:3].lower()}}},\n"
    f"  publisher = {{{P['publisher']}}},\n"
    f"  doi       = {{{DOI}}},\n"
    f"  url       = {{{DOI_URL}}}\n"
    f"}}\n"
)
RIS_LINES = ["TY  - GEN"]
RIS_LINES += [f'AU  - {a["family"]}, {a["initials"]}' for a in P["authors"]]
RIS_LINES += [
    f"TI  - {T}",
    f"PY  - {Y}",
    f"DA  - {Y}/{M:02d}/{D:02d}",
    f"PB  - {P['publisher']}",
    f"DO  - {DOI}",
    f"UR  - {DOI_URL}",
]
RIS_LINES += [f"KW  - {k}" for k in P.get("keywords", [])]
RIS_LINES.append("ER  - ")
RIS = "\n".join(RIS_LINES) + "\n"

# --------------------------------------------------------------------- css
CSS_CLASSIC = """
:root{--bg:#fff;--text:#1a1a1a;--muted:#4a4a4a;--link:#0b57d0;--card:#f4f6f9;--line:#d5d9e0;--btn:#0b57d0;--btn-text:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#121212;--text:#ececec;--muted:#b8b8b8;--link:#8ab4f8;--card:#1d1f23;--line:#3a3d44;--btn:#8ab4f8;--btn-text:#0b0b0b}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:17px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
a{color:var(--link);text-underline-offset:3px}
a:focus-visible,.btn:focus-visible{outline:3px solid var(--link);outline-offset:3px;border-radius:4px}
.skip{position:absolute;left:-999px;top:0;background:var(--btn);color:var(--btn-text);padding:.6rem 1rem;z-index:10}
.skip:focus{left:1rem;top:1rem}
.wrap{max-width:46rem;margin:0 auto;padding:0 1rem}
header.site{border-bottom:1px solid var(--line)}
header.site .wrap{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;align-items:center;justify-content:space-between;padding-top:.9rem;padding-bottom:.9rem}
.brand{font-weight:700;color:var(--text);text-decoration:none}
nav ul{display:flex;gap:1.25rem;list-style:none;margin:0;padding:0;flex-wrap:wrap}
nav a[aria-current=page]{color:var(--text);font-weight:600}
main{padding:2rem 0 3rem}
h1{font-size:clamp(1.6rem,5vw,2.3rem);line-height:1.2;margin:.4rem 0 1rem;letter-spacing:-.01em}
h2{font-size:1.4rem;margin:2.2rem 0 .6rem;line-height:1.3}
h3{font-size:1.15rem;margin:1.6rem 0 .4rem}
.eyebrow{color:var(--muted);font-size:.9rem;margin:0}
.byline{color:var(--muted);margin:0 0 1.2rem}
.actions{display:flex;flex-wrap:wrap;gap:.75rem;margin:1.2rem 0 0}
.btn{display:inline-block;padding:.7rem 1.1rem;border-radius:8px;background:var(--btn);color:var(--btn-text);font-weight:600;text-decoration:none}
.btn.alt{background:transparent;color:var(--link);border:2px solid var(--link)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem;margin:1rem 0}
dl{display:grid;grid-template-columns:max-content 1fr;gap:.5rem 1.2rem;margin:0}
dt{color:var(--muted)}
dd{margin:0;overflow-wrap:anywhere}
pre{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.9rem 1rem;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font:14.5px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;margin:.5rem 0 1rem}
.crumbs{font-size:.9rem;color:var(--muted);margin:0 0 .5rem}
.note{color:var(--muted);font-size:.95rem}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:.92rem;padding:1.5rem 0 2.5rem}
footer p{margin:.3rem 0}
@media (max-width:30rem){dl{grid-template-columns:1fr}dt{margin-top:.5rem}}
"""

CSS_CS = """
:root{color-scheme:dark light;--mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
--bg:#0d1117;--text:#e6edf3;--muted:#9da7b3;--link:#58a6ff;--card:#161b22;--line:#30363d;--btn:#58a6ff;--btn-text:#0d1117;
--accent:#3fb950;--code:#161b22;--kw:#ff7b72;--str:#a5d6ff;--cm:#8b949e;--num:#79c0ff;--fn:#d2a8ff}
@media (prefers-color-scheme:light){:root{--bg:#fff;--text:#1f2328;--muted:#59636e;--link:#0550ae;--card:#f6f8fa;--line:#d1d9e0;--btn:#0550ae;--btn-text:#fff;
--accent:#1a7f37;--code:#f6f8fa;--kw:#cf222e;--str:#0a3069;--cm:#59636e;--num:#0550ae;--fn:#6639ba}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:17px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
a{color:var(--link);text-underline-offset:3px}
a:focus-visible,.btn:focus-visible,pre:focus-visible{outline:3px solid var(--link);outline-offset:3px;border-radius:4px}
.skip{position:absolute;left:-999px;top:0;background:var(--btn);color:var(--btn-text);padding:.6rem 1rem;z-index:10}
.skip:focus{left:1rem;top:1rem}
.wrap{max-width:60rem;margin:0 auto;padding:0 1rem}
header.site{border-bottom:1px solid var(--line);background:var(--card)}
header.site .wrap{display:flex;flex-wrap:wrap;gap:.4rem 1.5rem;align-items:center;justify-content:space-between;padding-top:.8rem;padding-bottom:.8rem}
.brand{font:600 .95rem var(--mono);color:var(--text);text-decoration:none}
.prompt{color:var(--accent);margin-right:.6ch}
nav ul{display:flex;gap:1.2rem;list-style:none;margin:0;padding:0;flex-wrap:wrap}
nav a{font:.88rem var(--mono);color:var(--muted);text-decoration:none;padding-bottom:2px}
nav a:hover{color:var(--text)}
nav a[aria-current=page]{color:var(--text);border-bottom:2px solid var(--accent)}
main{padding:2.2rem 0 3.5rem}
main p,main ul,main ol{max-width:46rem}
h1{font:700 clamp(1.3rem,3.4vw,1.9rem)/1.25 var(--mono);letter-spacing:-.02em;margin:.5rem 0 .8rem}
h2{font:600 1.2rem/1.3 var(--mono);margin:2.6rem 0 .7rem}
h2::before{content:"## ";content:"## " / "";color:var(--accent)}
h3{font:600 1.02rem/1.35 var(--mono);margin:1.8rem 0 .4rem}
h3::before{content:"### ";content:"### " / "";color:var(--accent)}
.eyebrow{font:.85rem var(--mono);color:var(--muted);margin:0}
.byline{color:var(--muted);margin:0 0 1rem;font:.95rem var(--mono)}
.badges{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 1.2rem;padding:0;list-style:none}
.badge{display:inline-flex;font:.82rem/1 var(--mono);border:1px solid var(--line);border-radius:6px;overflow:hidden;text-decoration:none}
.badge span{padding:.45rem .6rem}
.badge span:first-child{background:var(--card);color:var(--muted)}
.badge span:last-child{color:var(--link)}
.actions{display:flex;flex-wrap:wrap;gap:.75rem;margin:1.2rem 0 0}
.btn{display:inline-block;padding:.65rem 1.05rem;border-radius:6px;background:var(--btn);color:var(--btn-text);font:600 .92rem var(--mono);text-decoration:none}
.btn.alt{background:transparent;color:var(--link);border:1px solid var(--link)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem;margin:1rem 0}
dl{display:grid;grid-template-columns:max-content 1fr;gap:.4rem 1rem;margin:0;font:.9rem/1.55 var(--mono)}
dt{color:var(--accent)}
dt::after{content:":";color:var(--muted)}
dd{margin:0;overflow-wrap:anywhere}
pre{background:var(--code);border:1px solid var(--line);border-radius:8px;padding:1rem;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font:13.5px/1.65 var(--mono);margin:.5rem 0 1rem;tab-size:4}
pre.numbered{white-space:pre;overflow-wrap:normal}
.l{display:block}
pre.numbered{counter-reset:ln}
pre.numbered .l{counter-increment:ln}
pre.numbered .l::before{content:counter(ln);display:inline-block;width:2ch;margin-right:1.6ch;text-align:right;color:var(--cm);-webkit-user-select:none;user-select:none}
.kw{color:var(--kw)}.st{color:var(--str)}.cm{color:var(--cm);font-style:italic}.nu{color:var(--num)}.fn{color:var(--fn)}
.hero-code{margin:1.8rem 0 .6rem}
.panes{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
.pane{border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--code);min-width:0}
.pane .bar{display:flex;align-items:center;gap:.8rem;padding:.55rem .9rem;border-bottom:1px solid var(--line);font:.8rem var(--mono);color:var(--muted);background:var(--card)}
.pane pre{border:0;border-radius:0;margin:0}
.dots{width:10px;height:10px;border-radius:50%;background:#ff5f56;box-shadow:16px 0 #ffbd2e,32px 0 #27c93f;margin-right:34px;flex:none}
.hero-code figcaption{color:var(--muted);font-size:.88rem;margin-top:.6rem;max-width:46rem}
.crumbs{font:.85rem var(--mono);color:var(--muted);margin:0 0 .5rem}
.note{color:var(--muted);font-size:.95rem}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:.9rem;padding:1.5rem 0 2.5rem}
footer p{margin:.3rem 0;max-width:46rem}
@media (max-width:48rem){.panes{grid-template-columns:1fr}}
@media (max-width:30rem){dl{grid-template-columns:1fr}dt{margin-top:.5rem}}
"""
CSS = CSS_CS if THEME == "cs" else CSS_CLASSIC


# ------------------------------------------------ code blocks + highlighter
PY_KW = {"def", "for", "in", "if", "return", "else", "elif", "while", "and", "or", "not", "None", "True", "False"}
PSEUDO_KW = {"FUNCTION", "SET", "TO", "FOR", "EACH", "IN", "IF", "THEN", "RETURN", "ELSE", "END", "WHILE", "DO", "FROM"}
TOKEN = re.compile(r'(#[^\n]*|//[^\n]*)|("[^"\n]*"|\'[^\'\n]*\')|\b(\d+)\b|\b([A-Za-z_][A-Za-z_0-9]*)\b')

DEMO_PSEUDO = """// Largest item in a list
FUNCTION find_max(numbers)
    SET best TO first item of numbers
    FOR EACH n IN numbers
        IF n > best THEN
            SET best TO n
    RETURN best"""
DEMO_PYTHON = """# Largest item in a list
def find_max(numbers):
    best = numbers[0]
    for n in numbers:
        if n > best:
            best = n
    return best"""


def hl_line(line, kws):
    out, pos = [], 0
    for m in TOKEN.finditer(line):
        out.append(esc(line[pos:m.start()]))
        pos = m.end()
        cm, st, nu, word = m.groups()
        if cm:
            out.append(f'<span class="cm">{esc(cm)}</span>')
        elif st:
            out.append(f'<span class="st">{esc(st)}</span>')
        elif nu:
            out.append(f'<span class="nu">{esc(nu)}</span>')
        elif word in kws:
            out.append(f'<span class="kw">{esc(word)}</span>')
        elif line[m.end():m.end() + 1] == "(":
            out.append(f'<span class="fn">{esc(word)}</span>')
        else:
            out.append(esc(word))
    out.append(esc(line[pos:]))
    return "".join(out)


def hl(code, kws):
    return "".join(f'<span class="l">{hl_line(l, kws)}\n</span>' for l in code.split("\n"))


def pre(text):
    """Plain code block; focusable so scrollable code is keyboard-reachable (AC-32)."""
    return f'<pre tabindex="0"><code>{esc(text)}</code></pre>'


def hero_html():
    def pane(name, label, inner, lang=""):
        return (f'<div class="pane"><div class="bar"><span class="dots" aria-hidden="true"></span><span>{name}</span></div>'
                f'<pre class="numbered" tabindex="0" aria-label="{label}"><code{lang}>{inner}</code></pre></div>')
    return (
        '<figure class="hero-code">\n<div class="panes">\n'
        + pane("pseudocode.txt", "Example pseudocode", hl(DEMO_PSEUDO, PSEUDO_KW)) + "\n"
        + pane("translated.py", "Equivalent Python code", hl(DEMO_PYTHON, PY_KW), ' class="language-python"') + "\n"
        '</div>\n<figcaption>Illustration of the task: pseudocode on the left, an equivalent Python translation on the right. '
        "This is a generic example, not output from the paper.</figcaption>\n</figure>"
    )


# ----------------------------------------------------------------- layout
NAV =[("", "Paper"), ("cite/", "Cite"), ("background/pseudocode-to-python/", "Background")]


def rel(path_from, path_to):
    if path_from == "404.html":  # served from any URL depth, so links must be root-absolute
        return "/" + path_to
    depth = len([s for s in path_from.split("/") if s])
    return ("../" * depth + path_to) if depth else (path_to or "./")


def layout(path, title, desc, body, jsonld, head_extra="", robots="index,follow", indexable=True):
    url = f"{SITE}/{path}"
    og_img = f"{SITE}/og-image.png"
    navhtml = "".join(
        f'<li><a href="{esc(rel(path, p))}"{" aria-current=\"page\"" if p == path else ""}>{esc(lbl)}</a></li>'
        for p, lbl in NAV
    )
    ld = "".join(
        f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>\n' for j in jsonld
    )
    og = ""
    canon = ""
    if indexable:
        canon = f'<link rel="canonical" href="{esc(url)}">\n'
        og = (
            f'<meta property="og:type" content="{"article" if path else "website"}">\n'
            f'<meta property="og:site_name" content="{esc(P["site_name"])}">\n'
            f'<meta property="og:title" content="{esc(title)}">\n'
            f'<meta property="og:description" content="{esc(desc)}">\n'
            f'<meta property="og:url" content="{esc(url)}">\n'
            f'<meta property="og:image" content="{esc(og_img)}">\n'
            f'<meta property="og:image:alt" content="{esc(P["short_title"])}: research paper by {esc(authors_natural())}">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n'
            f'<meta name="twitter:title" content="{esc(title)}">\n'
            f'<meta name="twitter:description" content="{esc(desc)}">\n'
            f'<meta name="twitter:image" content="{esc(og_img)}">\n'
        )
    icon = rel(path, "favicon.svg")
    return f"""<!doctype html>
<html lang="{P['language']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
{canon}<link rel="icon" href="{esc(icon)}" type="image/svg+xml">
<meta name="color-scheme" content="light dark">
{og}{head_extra}{ld}<style>{CSS}</style>
</head>
<body class="theme-{THEME}">
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap">
<a class="brand" href="{esc(rel(path, ''))}">{'<span class="prompt" aria-hidden="true">$</span>' if THEME == 'cs' else ''}{esc(P['short_title'])}</a>
<nav aria-label="Main"><ul>{navhtml}</ul></nav>
</div></header>
<main id="main"><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>Companion website for the paper <em>{esc(T)}</em>. The version of record is on Zenodo: <a href="{DOI_URL}">{DOI_URL}</a>.</p>
<p>Last updated {MODIFIED}.</p>
</div></footer>
</body>
</html>
"""


def breadcrumb(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": f"{SITE}/{p}"}
            for i, (n, p) in enumerate(items)
        ],
    }


def person(a):
    d = {"@type": "Person", "name": f'{a["initials"]} {a["family"]}', "familyName": a["family"]}
    if a.get("orcid"):
        d["sameAs"] = f'https://orcid.org/{a["orcid"]}'
    return d


# ------------------------------------------------------------------ pages
def page_home():
    path = ""
    pretty_date = f"{D} {MONTHS[M-1]} {Y}"
    keywords = P.get("keywords") or []
    head = ""
    for a in P["authors"]:
        head += f'<meta name="citation_author" content="{esc(a["family"])}, {esc(a["initials"])}">\n'
    head = (
        f'<meta name="citation_title" content="{esc(T)}">\n' + head +
        f'<meta name="citation_publication_date" content="{Y}/{M:02d}/{D:02d}">\n'
        f'<meta name="citation_doi" content="{esc(DOI)}">\n'
        f'<meta name="citation_publisher" content="{esc(P["publisher"])}">\n'
        f'<meta name="citation_language" content="{P["language_of_work"]}">\n'
    )
    if keywords:
        head += f'<meta name="citation_keywords" content="{esc("; ".join(keywords))}">\n'
    if P.get("pdf_url"):
        head += f'<meta name="citation_pdf_url" content="{esc(P["pdf_url"])}">\n'
    head += (
        f'<meta name="DC.title" content="{esc(T)}">\n'
        + "".join(f'<meta name="DC.creator" content="{esc(a["family"])}, {esc(a["initials"])}">\n' for a in P["authors"])
        + f'<meta name="DC.date" content="{P["date_published"]}">\n'
        f'<meta name="DC.identifier" content="{esc(DOI_URL)}">\n'
        f'<meta name="DC.publisher" content="{esc(P["publisher"])}">\n'
        f'<meta name="DC.type" content="Text">\n'
        f'<meta name="DC.language" content="{P["language_of_work"]}">\n'
    )

    article = {
        "@type": "ScholarlyArticle",
        "@id": f"{SITE}/#paper",
        "name": T,
        "headline": T,
        "author": [person(a) for a in P["authors"]],
        "datePublished": P["date_published"],
        "dateModified": MODIFIED,
        "identifier": {"@type": "PropertyValue", "propertyID": "DOI", "value": DOI},
        "url": f"{SITE}/",
        "sameAs": DOI_URL,
        "publisher": {"@type": "Organization", "name": P["publisher"], "url": "https://zenodo.org"},
        "inLanguage": P["language_of_work"],
        "isAccessibleForFree": True,
        "about": [{"@type": "Thing", "name": n} for n in
                  ["Pseudocode", "Python (programming language)", "Automated code generation"]],
    }
    if P.get("abstract"):
        article["abstract"] = P["abstract"]
        article["description"] = P["abstract"]
    if keywords:
        article["keywords"] = ", ".join(keywords)
    if P.get("license_url"):
        article["license"] = P["license_url"]
    website = {"@type": "WebSite", "@id": f"{SITE}/#website", "name": P["site_name"], "url": f"{SITE}/",
               "inLanguage": P["language"]}
    ld = [{"@context": "https://schema.org", "@graph": [website, article]}]

    abstract = (
        f'<h2>Abstract</h2>\n<p>{esc(P["abstract"])}</p>'
        if P.get("abstract")
        else f'<h2>About this paper</h2>\n<p>This is the companion website for the research paper '
             f'<em>{esc(T)}</em> by {esc(authors_natural())}, deposited on Zenodo on {pretty_date}. '
             f'The paper concerns translating pseudocode into executable Python through an algorithmic approach '
             f'to automated code generation. The full text and files are on the '
             f'<a href="{DOI_URL}">Zenodo record</a>.</p>'
    )
    rows = [
        ("Title", esc(T)),
        ("Authors", esc(authors_natural())),
        ("Published", f'<time datetime="{P["date_published"]}">{pretty_date}</time>'),
        ("Repository", esc(P["publisher"])),
        ("DOI", f'<a href="{DOI_URL}">{DOI}</a>'),
        ("Type", esc(P["resource_type"])),
        ("Language", "English"),
    ]
    if P.get("license_name"):
        lic = esc(P["license_name"])
        if P.get("license_url"):
            lic = f'<a href="{esc(P["license_url"])}">{lic}</a>'
        rows.append(("License", lic))
    if keywords:
        rows.append(("Keywords", esc(", ".join(keywords))))
    if P.get("pdf_url"):
        rows.append(("Full text", f'<a href="{esc(P["pdf_url"])}">PDF</a>'))
    dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    if THEME == "cs":
        badges = (f'<ul class="badges"><li><a class="badge" href="{DOI_URL}"><span>DOI</span><span>{esc(DOI)}</span></a></li>'
                  f'<li><a class="badge" href="{DOI_URL}"><span>repository</span><span>{esc(P["publisher"])}</span></a></li></ul>\n')
        hero = hero_html()
    else:
        badges = hero = ""

    body = f"""
<p class="eyebrow">{esc(P['resource_type'])} &middot; {esc(P['publisher'])} &middot; {pretty_date}</p>
<h1>{esc(T)}</h1>
<p class="byline">{esc(authors_natural())}</p>
{badges}<div class="actions">
<a class="btn" href="{DOI_URL}">Read the paper (DOI)</a>
<a class="btn alt" href="{esc(rel(path, 'cite/'))}">Cite this paper</a>
</div>
{hero}
{abstract}
<h2>Paper details</h2>
<div class="card"><dl>{dl}</dl></div>
<h2>Topic: translating pseudocode to Python</h2>
<p>Pseudocode describes an algorithm in structured, human-readable steps. Translating it to Python means producing
code that a computer can run. Automating that step is a code generation problem. If you are new to the area, the
<a href="{esc(rel(path, 'background/pseudocode-to-python/'))}">background guide to pseudocode-to-Python translation</a>
explains the main approaches and their trade-offs in plain language.</p>
<h2>How to cite</h2>
<p>Preferred citation (MLA):</p>
{pre(CITES['MLA'])}
<p>APA, Chicago, IEEE, BibTeX and RIS formats are on the <a href="{esc(rel(path, 'cite/'))}">citation page</a>.</p>
"""
    desc = (f"Reantaso et al. ({Y}), Translating Pseudocode to Python: An Algorithmic Approach to "
            f"Automated Code Generation. DOI, citation formats and topic guide.")
    return path, layout(path, T, desc, body, ld, head_extra=head)


def page_cite():
    path = "cite/"
    blocks = "".join(f"<h2>{k}</h2>\n{pre(v)}\n" for k, v in CITES.items())
    note = (
        '<p class="note">The author list on this site is incomplete (shown as &ldquo;et al.&rdquo;). '
        "Check the full author list on the Zenodo record before submitting a reference list.</p>"
        if P.get("authors_incomplete") else ""
    )
    body = f"""
<p class="crumbs"><a href="{esc(rel(path, ''))}">Paper</a> / Cite</p>
<h1>Cite &ldquo;{esc(P['short_title'])}&rdquo;</h1>
<p>Copy-ready references for <em>{esc(T)}</em> (Zenodo, {Y}), DOI
<a href="{DOI_URL}">{DOI}</a>.</p>
{note}
{blocks}
<h2>BibTeX</h2>
{pre(BIBTEX)}
<h2>RIS (Zotero, Mendeley, EndNote)</h2>
{pre(RIS)}
<p>Download: <a href="{esc(rel(path, 'paper.bib'))}">paper.bib</a> &middot; <a href="{esc(rel(path, 'paper.ris'))}">paper.ris</a></p>
"""
    desc = (f"Copy-ready APA, MLA, Chicago, IEEE, BibTeX and RIS citations for Reantaso et al., "
            f"Translating Pseudocode to Python, Zenodo {Y}, DOI {DOI}.")
    title = "Cite “Translating Pseudocode to Python” (APA, MLA, BibTeX)"
    ld = [breadcrumb([("Paper", ""), ("Cite", path)])]
    return path, layout(path, title, desc, body, ld)


def page_background():
    path = "background/pseudocode-to-python/"
    h1 = "Pseudocode to Python: How Automated Code Translation Works"
    body = f"""
<p class="crumbs"><a href="{esc(rel(path, ''))}">Paper</a> / Background</p>
<h1>{h1}</h1>
<p>Translating pseudocode to Python means turning a step-by-step description of an algorithm into code that a
computer can run. Doing it automatically is a form of <strong>automated code generation</strong>. This guide
explains the main approaches, their strengths and weaknesses, and how results are judged. It is general background
and does not summarise the findings of any particular paper.</p>

<h2>What is pseudocode?</h2>
<p>Pseudocode is an informal notation for describing algorithms. It borrows the structure of programming languages
(sequences, conditions, loops, functions) but ignores strict syntax, so people can focus on logic. It is common in
textbooks, exams, design documents and early prototyping. Because there is no single standard, two people can write
the same algorithm in very different styles.</p>

<h2>Why translate pseudocode to Python?</h2>
<ul>
<li><strong>Education:</strong> students can test an algorithm they have written without first mastering syntax.</li>
<li><strong>Prototyping:</strong> Python reads close to pseudocode, which makes it a natural first implementation.</li>
<li><strong>Specification to code:</strong> design documents often contain algorithm descriptions that someone must
implement by hand.</li>
</ul>

<h2>Approaches to automated translation</h2>
<h3>Rule-based and compiler-style translation</h3>
<p>This approach defines a grammar for the pseudocode, then processes it like a compiler: lexical analysis splits the
text into tokens, syntax analysis builds a tree, and code generation emits Python. The result is predictable and
explainable, but it only accepts pseudocode that follows the grammar. The open-source library
<a href="https://github.com/PseuToPy/PseuToPy">PseuToPy</a> is an example that converts instructions written in its
own pseudocode grammar into Python. A 2024 conference paper,
<a href="https://doi.org/10.1109/CSITSS64042.2024.10816767">Pseudocode to Python &ndash; A Compiler Approach</a>,
describes a compiler with lexical analysis, syntax analysis and code generation stages for introductory-level
constructs.</p>

<h3>Learned (machine-learning) translation</h3>
<p>Sequence-to-sequence and transformer models learn the mapping from examples of pseudocode paired with code. They
cope better with free-form wording, but need training data, can produce code that does not run, and are harder to
explain. Work in this area includes lightweight alternatives to large language models, such as models that copy
tokens that appear unchanged in both pseudocode and code, as well as fine-tuning large language models for
algorithm-to-Python translation. A 2023 IEEE conference review,
<a href="https://ieeexplore.ieee.org/abstract/document/10142254">Machine Learning for Translating Pseudocode to
Python: A Comprehensive Review</a>, surveys machine-learning methods for the task.</p>

<h3>Hybrid and search-based translation</h3>
<p>Some systems translate line by line, generate several candidate programs for each line, and then search for a
combination that compiles and passes tests. Combining structure-aware rules with learned components is a common
way to improve reliability.</p>

<h2>Why the problem is hard</h2>
<ul>
<li><strong>Ambiguity:</strong> &ldquo;repeat until done&rdquo; or &ldquo;process the list&rdquo; leaves the exact
loop or data structure unspecified.</li>
<li><strong>Scope and indentation:</strong> Python uses indentation for blocks, so a wrong nesting level changes
meaning.</li>
<li><strong>Types and libraries:</strong> pseudocode rarely states types, and may assume operations that need
imports.</li>
<li><strong>Verification:</strong> code can look right and still be wrong.</li>
</ul>

<h2>How translators are evaluated</h2>
<p>Text-similarity scores compare generated code to a reference, but they can reward code that is wrong and punish
code that is correct in a different style. Functional correctness is more informative: run the generated Python
against test cases and measure how many pass. The share of outputs that parse and run without errors is a useful
first filter.</p>

<h2>The paper this site accompanies</h2>
<p><em>{esc(T)}</em> by {esc(authors_natural())} is available on Zenodo:
<a href="{DOI_URL}">{DOI_URL}</a>. See the <a href="{esc(rel(path, ''))}">paper page</a> for details and the
<a href="{esc(rel(path, 'cite/'))}">citation page</a> for reference formats.</p>
"""
    desc = ("A plain-language guide to translating pseudocode to Python: rule-based compilers, machine learning, "
            "common challenges and how code generators are evaluated.")
    ld = [
        breadcrumb([("Paper", ""), ("Background", path)]),
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": h1,
            "description": desc,
            "datePublished": MODIFIED,
            "dateModified": MODIFIED,
            "inLanguage": P["language"],
            "mainEntityOfPage": f"{SITE}/{path}",
            "author": [person(a) for a in P["authors"]],
            "isPartOf": {"@id": f"{SITE}/#website"},
            "about": ["Pseudocode", "Python", "Automated code generation"],
        },
    ]
    return path, layout(path, h1, desc, body, ld)


def page_404():
    body = f"""
<h1>Page not found</h1>
<p>That page does not exist. Go to the <a href="/">paper page</a> or read the
<a href="/background/pseudocode-to-python/">background guide</a>.</p>
"""
    # 404 may be served at any depth, so it uses root-absolute links on purpose.
    html_out = layout("404.html", "Page not found | Translating Pseudocode to Python",
                      "The page you requested was not found on this site.", body, [],
                      robots="noindex,follow", indexable=False)
    return "404.html", html_out


# ------------------------------------------------------------- extra files
def write(relpath, content, mode="w"):
    full = os.path.join(DIST, relpath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, mode, **({"encoding": "utf-8"} if "b" not in mode else {})) as f:
        f.write(content)


def make_og_image():
    """Regenerate assets/og-image.png when Pillow is available; always copy it to dist (AC-37)."""
    asset = os.path.join(ROOT, "assets", "og-image.png")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        Image = None
    if Image is not None:
        bold = next(iter(sorted(glob.glob("/usr/share/fonts/**/DejaVuSansMono-Bold.ttf", recursive=True))), None)
        reg = next(iter(sorted(glob.glob("/usr/share/fonts/**/DejaVuSansMono.ttf", recursive=True))), None)
        if bold and reg:
            img = Image.new("RGB", (1200, 630), "#0d1117")
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, 1200, 56], fill="#161b22")
            for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
                d.ellipse([28 + i * 28, 20, 44 + i * 28, 36], fill=c)
            f_big, f_mid, f_sm = (ImageFont.truetype(bold, 50), ImageFont.truetype(reg, 28), ImageFont.truetype(reg, 26))
            d.text((60, 100), "$ pseudocode.txt  ->  translated.py", font=f_sm, fill="#3fb950")
            y = 170
            for line in textwrap.wrap(P["short_title"] + ":", 34):
                d.text((60, y), line, font=f_big, fill="#e6edf3")
                y += 66
            sub = P["title"].split(":", 1)[1].strip() if ":" in P["title"] else ""
            for line in textwrap.wrap(sub, 54):
                d.text((60, y + 10), line, font=f_mid, fill="#9da7b3")
                y += 42
            d.text((60, 520), authors_natural() + "  |  " + P["publisher"] + " " + str(Y), font=f_sm, fill="#58a6ff")
            d.text((60, 565), "doi.org/" + DOI, font=f_sm, fill="#9da7b3")
            os.makedirs(os.path.dirname(asset), exist_ok=True)
            img.save(asset, optimize=True)
    if os.path.exists(asset):
        os.makedirs(DIST, exist_ok=True)
        shutil.copyfile(asset, os.path.join(DIST, "og-image.png"))
        return True
    print("WARNING: no assets/og-image.png and Pillow unavailable; social preview image missing")
    return False


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    pages = [page_home(), page_cite(), page_background(), page_404()]
    for path, content in pages:
        out = "index.html" if path == "" else (path + "index.html" if path.endswith("/") else path)
        write(out, content)

    indexable = [p for p, _ in pages if p != "404.html"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in indexable:
        sm.append(f"  <url><loc>{esc(SITE + '/' + p)}</loc><lastmod>{MODIFIED}</lastmod></url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    write("llms.txt",
          f"# {P['short_title']}\n\n"
          f"> Companion website for the research paper \"{T}\" by {authors_natural()} "
          f"({P['publisher']}, {P['date_published']}). DOI: {DOI}\n\n"
          f"- [Paper page]({SITE}/): details, citation, DOI link\n"
          f"- [Citation formats]({SITE}/cite/): APA, MLA, Chicago, IEEE, BibTeX, RIS\n"
          f"- [Background guide]({SITE}/background/pseudocode-to-python/): how pseudocode-to-Python translation works\n"
          f"- [Version of record]({DOI_URL}): the paper on Zenodo\n")
    write("paper.bib", BIBTEX)
    write("paper.ris", RIS)
    write("favicon.svg",
          '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#0d1117"/>'
          '<text x="32" y="43" font-family="monospace" font-size="30" font-weight="700" text-anchor="middle" fill="#3fb950">&gt;_</text></svg>\n')
    og = make_og_image()
    print(f"Built {len(indexable)} indexable pages + 404 into {DIST} (site url: {SITE})"
          + ("" if og else "; og-image.png missing"))


if __name__ == "__main__":
    main()
