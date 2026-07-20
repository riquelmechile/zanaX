"""Investigación dentro de X: lee cuentas AI/dev que publican a diario.

Usa la API v2 de X con Bearer Token (X_BEARER_TOKEN). La lista de cuentas se
configura en X_ACCOUNTS (separada por comas, sin @). Con el plan Free no hay
lectura de API: si no hay token o falla, el nodo simplemente aporta 0 items y
el agente sigue con HN/GitHub/Reddit.
"""
from __future__ import annotations

import os

DEFAULT_ACCOUNTS = [
    "OpenAI", "GoogleDeepMind", "AnthropicAI", "huggingface", "LangChainAI",
    "kaboroevich", "_jasonwei", "DrJimFan", "svpino", "bindureddy",
]


def configured_accounts() -> list[str]:
    raw = os.getenv("X_ACCOUNTS", "")
    accounts = [a.strip().lstrip("@") for a in raw.split(",") if a.strip()]
    return accounts or DEFAULT_ACCOUNTS


def fetch_account_posts(limit_per_account: int = 3) -> list[dict]:
    """Tuits recientes (24-48h) de las cuentas configuradas, como tendencias.

    Devuelve items con el mismo formato que tools.gather_trends().
    """
    bearer = os.getenv("X_BEARER_TOKEN")
    if not bearer:
        return []
    try:
        import tweepy

        client = tweepy.Client(bearer_token=bearer)
        items = []
        for handle in configured_accounts():
            try:
                user = client.get_user(username=handle)
                if not user or not user.data:
                    continue
                tweets = client.get_users_tweets(
                    user.data.id, max_results=max(limit_per_account, 5),
                    tweet_fields=["public_metrics", "created_at"],
                    exclude=["retweets", "replies"],
                )
                for t in (tweets.data or [])[:limit_per_account]:
                    m = t.public_metrics or {}
                    items.append({
                        "source": f"x/@{handle}",
                        "title": t.text.replace("\n", " ")[:240],
                        "url": f"https://x.com/{handle}/status/{t.id}",
                        "score": m.get("like_count", 0) + 3 * m.get("retweet_count", 0),
                    })
            except Exception:
                continue
        return sorted(items, key=lambda x: -x["score"])
    except Exception:
        return []
