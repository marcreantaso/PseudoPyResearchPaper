# Deploy to Vercel

`vercel.json` already contains everything Vercel needs: build command, output directory, clean URLs, trailing slashes, security headers and a strict Content-Security-Policy.

## 1. Fill in the paper facts
Edit `data/paper.json` (abstract, keywords, all co-authors, `pdf_url`, license). See `DEPLOY.md` §1.
Pick the design with `"theme": "cs"` (default) or `"classic"`.

## 2. Put the project in Git
```
git init
git add .
git commit -m "Paper website"
```
Push to a new GitHub (or GitLab/Bitbucket) repository. `dist/` is git-ignored because Vercel builds it.

## 3. Import into Vercel
1. Vercel dashboard → **Add New → Project** → import the repository.
2. **Framework Preset:** Other. Leave the build command and output directory as detected from `vercel.json` (`python3 build.py --production`, `dist`).
3. **Environment Variables:** add `SITE_URL` = your final address, for example `https://reantaso-pseudocode.com`. This is what goes into canonical tags, the sitemap, Open Graph tags and JSON-LD. The `--production` build **fails on purpose** if the site URL is still a placeholder, so you cannot ship wrong canonicals by accident.
4. Deploy.

If you do not set `SITE_URL`, the build falls back to `site_url` in `paper.json`, then to Vercel's `VERCEL_PROJECT_PRODUCTION_URL`. Setting `SITE_URL` explicitly is the most reliable option.

## 4. Custom domain (recommended for ranking)
Project → **Settings → Domains** → add your domain, then set the DNS records Vercel shows. Pick one canonical host (for example the apex, with `www` redirecting to it) and use exactly that in `SITE_URL`. Redeploy after changing it.

## 5. Tell search engines
Use the **production** domain, never a `*.vercel.app` preview URL (Vercel marks preview deployments `noindex`).
1. Google Search Console → add the property → submit `https://<domain>/sitemap.xml` → request indexing for `/`.
2. Bing Webmaster Tools → import from Search Console or submit the sitemap.
3. Then follow `DEPLOY.md` §4: link to the site from the Zenodo record, ORCID, Google Scholar, GitHub and your institution page.

## If the Vercel build cannot find Python
Build locally instead and deploy the output:
```
SITE_URL=https://your-domain python3 build.py --production
npx vercel deploy --prebuilt   # or: npx vercel --prod dist
```
Or remove `buildCommand` from `vercel.json`, remove `dist/` from `.gitignore`, commit the built `dist/`, and set the project's Output Directory to `dist`.

## Social preview image
`assets/og-image.png` is committed so Vercel builds work without Pillow. It is regenerated locally whenever Pillow and DejaVu fonts are present, so after changing the title or authors run `python3 build.py` once on your machine and commit the new `assets/og-image.png`.

## Checks
```
SITE_URL=https://your-domain python3 build.py --production
SITE_URL=https://your-domain python3 verify.py
```
