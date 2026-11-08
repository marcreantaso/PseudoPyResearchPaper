# SPEC — Research Paper Website

**Paper:** Reantaso, M. G., et al. "Translating Pseudocode to Python: An Algorithmic Approach to Automated Code Generation." Zenodo, 6 Nov. 2026. https://doi.org/10.5281/zenodo.24006170

**Spec status:** v1.0 — written before any code. `build.py` implements it, `verify.py` checks it.

---

## 1. Purpose

A fast, static, indexable website that gives the paper a second discoverable home beyond the Zenodo record, so that people searching for the paper's topic or title find it and are sent to the DOI as the version of record.

**Non-goals:** hosting a rival copy of the full text; guaranteeing a ranking position (nobody can); JavaScript apps, trackers, or logins.

## 2. Principles

| # | Principle | Consequence |
|---|-----------|-------------|
| P1 | Single source of truth | All paper facts live in `data/paper.json`. No fact is typed twice in templates. |
| P2 | Never invent | Fields not supplied (abstract, co-authors, keywords, PDF URL) are omitted from output, never fabricated. `verify.py` lists them as TODOs. |
| P3 | DOI is canonical for the paper | The site links to the DOI everywhere the paper is cited. The site's own pages are canonical to themselves and earn ranking through unique value (cite tools, topic explainer), not by cloning Zenodo. |
| P4 | Static + zero JS | Plain HTML/CSS, system fonts, no third-party requests. |
| P5 | Spec before code | Every requirement below has an ID; `verify.py` reports pass/fail per ID. |

## 3. Keyword strategy

| Tier | Target queries | Where they appear |
|------|----------------|-------------------|
| Exact title | "Translating Pseudocode to Python: An Algorithmic Approach to Automated Code Generation" | `<title>` of home, H1, JSON-LD `name`, citation meta |
| Primary | translating pseudocode to Python; pseudocode to Python translation; automated code generation from pseudocode | Home H1/H2, meta description, background article H1 |
| Secondary | pseudocode to Python converter; pseudocode compiler; algorithmic code generation; natural-language pseudocode to code | Background article headings and body |
| Navigational | Reantaso pseudocode Python; zenodo 10.5281/zenodo.24006170; DOI string | Home, cite page, JSON-LD `identifier` |

## 4. Page inventory

| Path | Intent | Required content |
|------|--------|------------------|
| `/` | Paper landing page | H1 = exact title; authors; date; DOI button; abstract (if provided); keywords; "Cite this paper" summary; link to Cite page and Background |
| `/cite/` | Citation tool | APA, MLA, Chicago, IEEE, BibTeX, RIS; downloadable `paper.bib` and `paper.ris` |
| `/background/pseudocode-to-python/` | Informational search intent | Original explainer on translating pseudocode to Python (rule-based/compiler vs. learned approaches), with outbound links to authoritative related work. Makes **no claims** about the paper's results. |
| `/404.html` | Error page | Link home, `noindex` |
| `/sitemap.xml`, `/robots.txt`, `/llms.txt` | Crawler files | See §6 |

## 5. Functional requirements and acceptance criteria

### 5.1 On-page SEO
- **AC-01** Every indexable page has exactly one `<h1>`.
- **AC-02** Home `<h1>` equals `paper.title` exactly.
- **AC-03** Every `<title>` is unique and 20–65 characters. The home title is the exact paper title (85 characters) so it may be up to 90; search engines index the full title and only truncate the display.
- **AC-04** Every page has a `meta description` of 70–160 characters, unique per page.
- **AC-05** Every page has a self-referencing `rel="canonical"` using the configured site URL.
- **AC-06** `<html lang="en">` and viewport meta present on every page.
- **AC-07** Open Graph (`og:title`, `og:description`, `og:type`, `og:url`, `og:image`) and Twitter card tags on every indexable page.
- **AC-08** Headings never skip a level (h1 → h2 → h3).
- **AC-09** Every `<img>` has non-empty `alt`.

### 5.2 Scholarly metadata
- **AC-10** Home page carries Highwire Press tags: `citation_title`, `citation_author` (one per known author), `citation_publication_date`, `citation_doi`, `citation_publisher`, plus `citation_pdf_url` only if supplied.
- **AC-11** Home page carries Dublin Core tags: `DC.title`, `DC.creator`, `DC.date`, `DC.identifier` (DOI URL), `DC.publisher`.
- **AC-12** Home page has valid JSON-LD `ScholarlyArticle` with `name`, `author`, `datePublished`, `identifier` (PropertyValue, `propertyID: DOI`), `url`, `sameAs` (DOI URL), `publisher`, `inLanguage`, and `keywords` only if supplied.
- **AC-13** Subpages carry JSON-LD `BreadcrumbList`; background page also carries `Article` JSON-LD.
- **AC-14** Every JSON-LD block parses as JSON.

### 5.3 Crawlability
- **AC-15** `sitemap.xml` lists every indexable page with absolute URLs and `lastmod`; excludes 404.
- **AC-16** `robots.txt` allows all and references the sitemap by absolute URL.
- **AC-17** `404.html` has `noindex`.
- **AC-18** Every internal link resolves to a built file.
- **AC-19** Every page is reachable from the home page within 2 clicks.

### 5.4 Performance and accessibility
- **AC-20** No external requests (scripts, fonts, stylesheets, trackers). Outbound `<a>` links are allowed.
- **AC-21** No JavaScript.
- **AC-22** Each HTML file ≤ 60 KB.
- **AC-23** A "skip to content" link, landmark elements (`header`, `nav`, `main`, `footer`), and visible focus styles.
- **AC-24** Text/background contrast ≥ 4.5:1 in light and dark themes (`prefers-color-scheme`).
- **AC-25** Layout works at 320 px width with no horizontal scroll (fluid layout, no fixed widths over 100%).

### 5.5 Integrity
- **AC-26** The DOI string `10.5281/zenodo.24006170` appears on home and cite pages and every DOI link is `https://doi.org/10.5281/zenodo.24006170`.
- **AC-27** The site URL is not a placeholder before deploy (warning-level until `site_url` is set).
- **AC-28** No invented facts: abstract, co-authors, keywords and PDF URL render only when present in `paper.json` (warning-level list of missing optional fields).

## 6. Crawler files
- `robots.txt`: `User-agent: *`, `Allow: /`, `Sitemap: <site>/sitemap.xml`.
- `llms.txt`: plain-language summary and key URLs, for AI search and answer engines.
- `sitemap.xml`: sitemap protocol 0.9.

## 7. Build design
```
data/paper.json   ← single source of truth (edit this)
build.py          ← renders dist/ from paper.json (stdlib only)
verify.py         ← checks AC-01…AC-28 against dist/
dist/             ← deployable static site
DEPLOY.md         ← hosting + indexing steps
```

## 8. Off-site actions (cannot be automated here, required for ranking)
1. Host `dist/` on a domain you control (GitHub Pages, Netlify, Cloudflare Pages).
2. Verify the domain in Google Search Console and Bing Webmaster Tools; submit `sitemap.xml`.
3. Link to the site from the Zenodo record description, ORCID, GitHub README, Google Scholar profile, institutional page.
4. Fill in the abstract, full author list and keywords in `paper.json`, rebuild, redeploy.

## 9. Design theme "cs" (v1.1)
`data/paper.json` gains `"theme": "cs" | "classic"`. `cs` is the default; `classic` is the original plain design and must keep passing every check.

Audience: computer scientists, software engineers and students who read papers on a laptop, often in dark mode, and who expect to copy things.

Design principles for `cs`:
- Code-editor look: monospace for headings, labels and navigation; system sans-serif for long reading text.
- Dark by default with a light scheme via `prefers-color-scheme`; both are first-class.
- Home hero shows a side-by-side **pseudocode → Python** illustration of the task, syntax-highlighted at build time (no JavaScript) and clearly labelled as an illustration, not output from the paper (P2).
- Paper metadata rendered as a key/value block (`title:`, `authors:`, `doi:` …) using a real `<dl>`.
- Citation formats appear in code-style blocks with a format label.

- **AC-29** `cs` theme defines a monospace stack, a dark scheme, and a light scheme under `prefers-color-scheme`.
- **AC-30** Home hero contains a `<figure>` with a `<figcaption>` stating it is an illustration and not output of the paper, and two `<pre><code>` blocks (pseudocode and Python).
- **AC-31** Every syntax colour (keyword, string, comment, number, function, plain) has contrast ≥ 4.5:1 on the code background in both schemes.
- **AC-32** Every `<pre>` is keyboard-focusable (`tabindex="0"`) so scrollable code can be reached without a mouse.
- **AC-33** Line numbers are generated by CSS and are not selectable, so copying code never copies them.

## 10. Hosting on Vercel (v1.1)
- **AC-34** `vercel.json` exists, parses as JSON, sets `outputDirectory: "dist"`, `buildCommand`, `cleanUrls: true`, `trailingSlash: true`.
- **AC-35** `vercel.json` sets security headers on all routes: `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and a `Content-Security-Policy` that forbids scripts, external requests and framing.
- **AC-36** The canonical/sitemap site URL resolves in this order: `--site-url` flag, `SITE_URL` env var, `site_url` in `paper.json` (if not a placeholder), `VERCEL_PROJECT_PRODUCTION_URL` env var. A build with only a placeholder fails loudly when `--production` is passed.
- **AC-37** The build succeeds without Pillow by using a committed `assets/og-image.png`; with Pillow it regenerates that file.
- **AC-38** Internal links stay correct under `cleanUrls` and `trailingSlash` (pages are `dir/index.html`, linked with trailing slashes).

## 11. Definition of done
`python3 verify.py` exits 0 with every FAIL resolved, for the default theme and for `--theme classic`. Warnings (AC-27, AC-28) are allowed but are reported to the owner.
