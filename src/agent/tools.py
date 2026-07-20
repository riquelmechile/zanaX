"""Fuentes de tendencias AI/dev: Hacker News, GitHub Trending, Reddit y búsqueda web."""
from __future__ import annotations

import feedparser
import httpx
from duckduckgo_search import DDGS


def hackernews_top(limit: int = 15) -> list[dict]:
    """Top stories de Hacker News filtradas por relevancia AI/dev."""
    r = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=20)
    ids = r.json()[:60]
    items = []
    for sid in ids:
        try:
            it = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=10).json()
            if it and it.get("title"):
                items.append({
                    "source": "hackernews",
                    "title": it["title"],
                    "url": it.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                    "score": it.get("score", 0),
                })
        except Exception:
            continue
        if len(items) >= limit:
            break
    return items


def github_trending() -> list[dict]:
    """Repos trending de GitHub vía RSS de trending (no oficial pero estable)."""
    items = []
    for url in [
        "https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml",
    ]:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:10]:
                items.append({"source": "github", "title": e.title, "url": e.link, "score": 0})
        except Exception:
            continue
    return items


def reddit_ai(limit: int = 10) -> list[dict]:
    """Posts calientes de subreddits de AI/dev (JSON público)."""
    subs = ["MachineLearning", "LocalLLaMA", "artificial", "webdev", "programming"]
    items = []
    headers = {"User-Agent": "x-ai-agent/1.0"}
    for sub in subs:
        try:
            r = httpx.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=5",
                          headers=headers, timeout=15)
            for c in r.json()["data"]["children"]:
                d = c["data"]
                items.append({
                    "source": f"r/{sub}",
                    "title": d["title"],
                    "url": f"https://reddit.com{d['permalink']}",
                    "score": d.get("score", 0),
                })
        except Exception:
            continue
    return sorted(items, key=lambda x: -x["score"])[:limit]


def web_search(query: str, limit: int = 5) -> list[dict]:
    """Búsqueda web para contexto adicional de una tendencia."""
    try:
        with DDGS() as ddgs:
            return [
                {"source": "web", "title": r["title"], "url": r["href"],
                 "snippet": r.get("body", "")}
                for r in ddgs.news(query, max_results=limit)
            ]
    except Exception:
        return []


def gather_trends() -> list[dict]:
    trends = hackernews_top() + github_trending() + reddit_ai()
    # dedupe por título normalizado
    seen, out = set(), []
    for t in trends:
        k = t["title"].lower()[:60]
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out
