"""Web search layer: SearchClient interface + Tavily implementation + offline mock.

Tavily chosen as primary: LLM-oriented results with pre-cleaned `content` and
optional `raw_content` full text (so most pages need no separate fetch), plain
REST via requests (no SDK), and server-side exclude_domains (leakage layer 1).
"""
from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import requests

from src.agentic import config as AC


@dataclass
class SearchResult:
    url: str
    title: str
    content: str                     # provider snippet / cleaned excerpt
    raw_content: str | None = None   # full page text when the provider returns it
    score: float = 0.0


class SearchClient:
    def search(self, query: str, max_results: int = AC.SEARCH_MAX_RESULTS,
               exclude_domains: list[str] | None = None) -> list[SearchResult]:
        raise NotImplementedError


class TavilySearchClient(SearchClient):
    ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get(AC.TAVILY_ENV, "")
        if not self.api_key:
            raise ValueError(f"no Tavily key: set {AC.TAVILY_ENV} in .env")

    def search(self, query: str, max_results: int = AC.SEARCH_MAX_RESULTS,
               exclude_domains: list[str] | None = None) -> list[SearchResult]:
        payload = {
            "api_key": self.api_key,            # legacy body auth (harmless with header)
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_raw_content": True,
            "exclude_domains": exclude_domains or [],
        }
        resp = requests.post(
            self.ENDPOINT, json=payload, timeout=AC.FETCH_TIMEOUT_S * 2,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()
        out = []
        for r in data.get("results", []):
            out.append(SearchResult(
                url=r.get("url", ""), title=r.get("title", ""),
                content=r.get("content", "") or "",
                raw_content=r.get("raw_content") or None,
                score=float(r.get("score", 0.0) or 0.0),
            ))
        return out


@dataclass
class MockSearchClient(SearchClient):
    """Fixture-backed offline search for smoke tests.

    Fixture format: {"<keyword>": [result, ...], "default": [result, ...]} where a
    query is served by the first keyword it contains (else "default"). Each result
    dict: url, title, content, raw_content?, score?.
    """
    fixture_path: Path = field(default_factory=lambda: Path(__file__).parent / "tests" / "fixtures" / "search_fixtures.json")
    _data: dict = field(default=None, repr=False)

    def _load(self) -> dict:
        if self._data is None:
            self._data = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        return self._data

    def search(self, query: str, max_results: int = AC.SEARCH_MAX_RESULTS,
               exclude_domains: list[str] | None = None) -> list[SearchResult]:
        data = self._load()
        low = query.lower()
        rows = None
        for key, results in data.items():
            if key != "default" and key.lower() in low:
                rows = results
                break
        if rows is None:
            rows = data.get("default", [])
        out = [SearchResult(url=r["url"], title=r["title"], content=r.get("content", ""),
                            raw_content=r.get("raw_content"), score=float(r.get("score", 0.5)))
               for r in rows[:max_results]]
        # honor exclude_domains like the real provider (layer 1)
        if exclude_domains:
            out = [r for r in out if not any(d in r.url for d in exclude_domains)]
        return out


class WikipediaSearchClient(SearchClient):
    """Keyless fallback when no Tavily key is configured.

    Uses the public MediaWiki API: full-text search + plain-text extracts (which
    become raw_content, so no HTML fetching is needed). Weaker than a real search
    engine for CPC/official sources, but keeps the collection agent functional.
    """
    API = "https://en.wikipedia.org/w/api.php"
    # Wikimedia blocks default python-requests UA with 403 — a descriptive UA is required.
    UA = {"User-Agent": "PatentLandscapingResearch/1.0 (academic project; leesuin9209@gmail.com)"}

    def search(self, query: str, max_results: int = AC.SEARCH_MAX_RESULTS,
               exclude_domains: list[str] | None = None) -> list[SearchResult]:
        try:
            r = requests.get(self.API, timeout=AC.FETCH_TIMEOUT_S, headers=self.UA, params={
                "action": "query", "list": "search", "srsearch": query,
                "srlimit": max_results, "format": "json"})
            r.raise_for_status()
            hits = r.json().get("query", {}).get("search", [])
        except requests.RequestException as e:
            print(f"  [search] wikipedia search failed: {e!r}")
            return []
        out = []
        titles = [h["title"] for h in hits]
        extracts = self._extracts(titles)
        for h in hits:
            title = h["title"]
            url = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
            if exclude_domains and any(d in url for d in exclude_domains):
                continue
            snippet = re.sub(r"<[^>]+>", "", h.get("snippet", ""))
            out.append(SearchResult(url=url, title=title, content=snippet,
                                    raw_content=extracts.get(title),
                                    score=1.0 / (1 + len(out))))
        return out

    def _extracts(self, titles: list[str]) -> dict[str, str]:
        if not titles:
            return {}
        try:
            # exintro: full-text extracts are limited to 1 page/request by MediaWiki;
            # intro sections batch fine and carry the definitional content we need.
            r = requests.get(self.API, timeout=AC.FETCH_TIMEOUT_S * 2, headers=self.UA, params={
                "action": "query", "prop": "extracts", "explaintext": 1, "exintro": 1,
                "exlimit": "max", "titles": "|".join(titles[:20]), "format": "json",
                "redirects": 1})
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            return {p.get("title", ""): p.get("extract", "") or None
                    for p in pages.values()}
        except requests.RequestException as e:
            print(f"  [search] wikipedia extracts failed: {e!r}")
            return {}


def make_search_client(mock: bool = False) -> SearchClient:
    if mock:
        return MockSearchClient()
    from dotenv import load_dotenv
    load_dotenv(AC.ROOT / ".env", override=False)
    if os.environ.get(AC.TAVILY_ENV, ""):
        return TavilySearchClient()
    print(f"  [search] no {AC.TAVILY_ENV} — falling back to keyless Wikipedia search")
    return WikipediaSearchClient()
