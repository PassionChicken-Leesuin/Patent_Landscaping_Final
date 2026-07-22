"""Page-content acquisition: prefer the provider's raw_content, else fetch+parse.

Parser is BeautifulSoup with the built-in "html.parser" (pure Python — no lxml,
which has C-extension wheel risk on Python 3.14/Windows). Failures are never
fatal: the caller skips the page.
"""
from __future__ import annotations

import requests

from src.agentic import config as AC
from src.agentic.search import SearchResult

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

_DROP_TAGS = ("script", "style", "nav", "footer", "header", "aside", "form", "noscript")
_KEEP_TAGS = ("h1", "h2", "h3", "p", "li")


def _clean(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def extract_html_text(html: str) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_DROP_TAGS):
        tag.decompose()
    parts = [el.get_text(" ", strip=True) for el in soup.find_all(_KEEP_TAGS)]
    parts = [p for p in parts if len(p) > 30]        # drop boilerplate crumbs
    if not parts:                                    # fallback: whole-page text
        return _clean(soup.get_text("\n"))
    return "\n".join(parts)


def fetch_url_text(url: str) -> str | None:
    for _ in range(2):                               # one retry
        try:
            resp = requests.get(url, timeout=AC.FETCH_TIMEOUT_S,
                                headers={"User-Agent": _UA})
            if resp.status_code != 200 or "text/html" not in resp.headers.get("content-type", "text/html"):
                return None
            return extract_html_text(resp.text)
        except requests.RequestException:
            continue
    return None


def page_text(result: SearchResult) -> tuple[str, str] | None:
    """Return (text, source) where source ∈ {provider_raw, fetched, provider_short, snippet}.
    A short raw_content (e.g. a Wikipedia intro extract) is upgraded to the full page
    via HTML fetch when possible — body sections carry the taxonomy/technique detail."""
    if result.raw_content and len(result.raw_content) > 1500:
        return result.raw_content[:AC.PAGE_TEXT_CHARS], "provider_raw"
    fetched = fetch_url_text(result.url)
    if fetched and len(fetched) > 300:
        return fetched[:AC.PAGE_TEXT_CHARS], "fetched"
    if result.raw_content and len(result.raw_content) > 300:
        return result.raw_content[:AC.PAGE_TEXT_CHARS], "provider_short"
    if result.content and len(result.content) > 200:
        return result.content[:AC.PAGE_TEXT_CHARS], "snippet"
    return None
