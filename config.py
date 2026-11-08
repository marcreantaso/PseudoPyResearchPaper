"""Shared configuration resolution for build.py and verify.py (SPEC AC-36)."""
import os
import sys

PLACEHOLDER = "YOUR-DOMAIN"


def _flag(argv, name):
    return argv[argv.index(name) + 1] if name in argv else None


def _normalise(url):
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def site_url(argv, paper):
    """Order: --site-url, SITE_URL env, paper.json (if not placeholder), VERCEL_PROJECT_PRODUCTION_URL."""
    v = _flag(argv, "--site-url")
    if v:
        return _normalise(v)
    v = os.environ.get("SITE_URL")
    if v:
        return _normalise(v)
    v = paper.get("site_url", "")
    if v and PLACEHOLDER not in v:
        return _normalise(v)
    v = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
    if v:
        return _normalise(v)
    return _normalise(v or paper.get("site_url", "https://" + PLACEHOLDER + ".example"))


def theme(argv, paper):
    t = _flag(argv, "--theme") or paper.get("theme", "cs")
    if t not in ("cs", "classic"):
        sys.exit(f"Unknown theme {t!r}; use 'cs' or 'classic'")
    return t


def check_production(argv, url):
    if "--production" in argv and PLACEHOLDER in url:
        sys.exit(
            "ERROR: site URL is still a placeholder. Set the SITE_URL environment variable "
            "(Vercel: Settings -> Environment Variables), or site_url in data/paper.json."
        )
