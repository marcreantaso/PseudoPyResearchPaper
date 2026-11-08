# Deploy and get indexed

> Hosting on Vercel? Follow **DEPLOY-VERCEL.md** for the hosting steps, then come back here for indexing and link-building (§3 onward).

Nothing here can be done from inside this chat; these are the steps that actually move the site into search results.

## 1. Fill in the facts (5 minutes)
Edit `data/paper.json`:
- `site_url`: the real domain, e.g. `https://reantaso-pseudocode.github.io` or your own domain
- `abstract`: paste the abstract from the Zenodo record
- `keywords`: the keywords from the Zenodo record
- `authors` and `authors_incomplete`: add every co-author as `{"family": "...", "initials": "...", "orcid": "0000-0000-0000-0000"}`, then set `authors_incomplete` to `false`
- `pdf_url`: the direct Zenodo file URL (for example `https://zenodo.org/records/24006170/files/<file>.pdf`)
- `license_name` and `license_url`: from the Zenodo record
- `date_modified`: today's date whenever you rebuild

Then:
```
python3 build.py
python3 verify.py        # must say 0 fail; warnings tell you what is still missing
```

## 2. Host `dist/`
Any static host works. Easiest options:
- **GitHub Pages:** push the contents of `dist/` to a repo, Settings → Pages. Use a custom domain or a `username.github.io` site so links work from the root.
- **Cloudflare Pages / Netlify:** drag-and-drop the `dist/` folder.

Serve over HTTPS. Make the host return `404.html` for missing pages.

## 3. Tell search engines
1. **Google Search Console** → add the property → verify (DNS or HTML tag) → Sitemaps → submit `https://<your-domain>/sitemap.xml` → URL Inspection → "Request indexing" for `/`.
2. **Bing Webmaster Tools** → import from Search Console, or add and verify the site, then submit the sitemap.
3. Optional: IndexNow (supported by Bing and others) for faster discovery of changes.

## 4. Earn links (the part that decides ranking)
A new site with no inbound links ranks poorly whatever its HTML. Link to it from places you control:
- The **Zenodo record** (edit → Related works / description: add the site URL)
- Your **ORCID** profile, **Google Scholar** profile, **ResearchGate/Academia**
- Your **GitHub** repository README, if the paper has code
- Your **institution or department** page, and your co-authors' pages
- A short post on LinkedIn or a relevant community, linking the DOI and this site

## 5. Keep it honest and unique
- Keep the DOI as the version of record. The site links to it everywhere.
- Do not paste the whole paper onto the site; duplicate text competes with Zenodo and can be filtered out. The background guide and citation tools are what make this site worth indexing.
- Add new original pages over time (for example a worked example, a glossary, a FAQ) by extending `build.py` and `SPEC.md` first, then `verify.py`.

## 6. After a few weeks
Search Console → Performance shows which queries bring impressions. Adjust page titles, headings and the background guide to the queries you actually see.
