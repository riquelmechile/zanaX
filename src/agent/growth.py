"""Crecimiento en X: descubrir cuentas afines, seguir, dejar de seguir, comentar.

LÍMITES (uso personal, coste optimizado pay-per-use 2026):
- Seguir: máx. FOLLOW_PER_DAY/día (def. 25 ≈ $12/mes) en tandas de FOLLOW_BATCH
  (def. 7) con pausas aleatorias de 30-60s entre follows (anti-ráfagas)
- Dejar de seguir: máx. UNFOLLOW_PER_WEEK/semana (def. 50) en dosis diarias de
  UNFOLLOW_BATCH (def. 7) y nunca cuentas en whitelist (X_NEVER_UNFOLLOW)
- Comentarios: SIEMPRE pasan por aprobación en Telegram; el agente solo redacta

Requiere X_BEARER_TOKEN (lectura) y las 4 claves OAuth1 (acciones).
"""
from __future__ import annotations

import json
import os
import pathlib
import random
import time
from datetime import datetime, timedelta, timezone

DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "/tmp/zanax-data"))
GROWTH = DATA_DIR / "growth.json"

NICHE_QUERIES = ["AI agents", "LLM", "open source AI", "machine learning",
                 "dev tools", "vibe coding"]


def _load() -> dict:
    try:
        return json.loads(GROWTH.read_text())
    except Exception:
        return {"follows": [], "unfollows": [], "commented": []}


def _save(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GROWTH.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _oauth_client():
    import tweepy
    return tweepy.Client(
        bearer_token=os.environ.get("X_BEARER_TOKEN"),
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )


def _count_today(entries: list[dict], days: int = 1) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    n = 0
    for e in entries:
        try:
            if datetime.fromisoformat(e["at"]) >= cutoff:
                n += 1
        except Exception:
            pass
    return n


# ---------- DESCUBRIR ----------

def discover_accounts(limit: int = 20) -> list[dict]:
    """Busca cuentas afines al nicho con engagement real, vía recent search."""
    if not os.getenv("X_BEARER_TOKEN"):
        return []
    try:
        client = _oauth_client()
        data = _load()
        already = {f["id"] for f in data["follows"]}
        found: dict[str, dict] = {}
        for q in NICHE_QUERIES[:4]:
            try:
                resp = client.search_recent_tweets(
                    query=f"({q}) lang:en -is:retweet -is:reply",
                    max_results=20,
                    tweet_fields=["public_metrics", "author_id"],
                    expansions=["author_id"],
                    user_fields=["username", "public_metrics", "description"],
                )
            except Exception:
                continue
            users = {u.id: u for u in (resp.includes or {}).get("users", [])}
            for t in (resp.data or []):
                u = users.get(t.author_id)
                if not u or str(u.id) in already:
                    continue
                followers = (u.public_metrics or {}).get("followers_count", 0)
                if followers < 500:  # filtra bots/cuentas sin tracción
                    continue
                eng = (t.public_metrics or {}).get("like_count", 0)
                key = str(u.id)
                if eng > found.get(key, {}).get("engagement", -1):
                    found[key] = {
                        "id": key, "handle": u.username,
                        "followers": followers, "engagement": eng,
                        "bio": (u.description or "")[:120],
                    }
        ranked = sorted(found.values(), key=lambda x: -x["engagement"])
        return ranked[:limit]
    except Exception:
        return []


# ---------- SEGUIR / DEJAR DE SEGUIR ----------

def follow_top(limit: int | None = None) -> list[str]:
    """Sigue las mejores cuentas descubiertas, respetando el tope diario.

    Pausas aleatorias de 30-60s entre follows: las ráfagas (>30-50/hora) son
    la señal #1 que detecta el anti-spam de X. El scheduler llama a esta
    función varias veces al día con tandas pequeñas.
    """
    cap = limit or int(os.getenv("FOLLOW_PER_DAY", "25"))
    batch = int(os.getenv("FOLLOW_BATCH", "7"))
    data = _load()
    remaining = min(batch, cap - _count_today(data["follows"]))
    if remaining <= 0:
        return []
    followed = []
    try:
        me = _oauth_client().get_me()
        my_id = me.data.id
        client = _oauth_client()
        for acc in discover_accounts():
            if len(followed) >= remaining:
                break
            try:
                client.follow_user(acc["id"], user_auth=True)
                data["follows"].append({
                    "id": acc["id"], "handle": acc["handle"],
                    "at": datetime.now(timezone.utc).isoformat(),
                })
                followed.append(acc["handle"])
                time.sleep(random.uniform(30, 60))
            except Exception:
                continue
        _save(data)
    except Exception:
        pass
    return followed


def prune_following() -> list[str]:
    """Deja de seguir cuentas que no devolvieron el follow tras 7 días.

    Conservador: tope semanal en dosis diarias y nunca toca la whitelist
    X_NEVER_UNFOLLOW.
    """
    cap = int(os.getenv("UNFOLLOW_PER_WEEK", "50"))
    batch = int(os.getenv("UNFOLLOW_BATCH", "7"))  # dosis diaria
    never = {h.strip().lstrip("@").lower()
             for h in os.getenv("X_NEVER_UNFOLLOW", "").split(",") if h.strip()}
    data = _load()
    remaining = min(batch, cap - _count_today(data["unfollows"], days=7))
    if remaining <= 0:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    unfollowed = []
    try:
        client = _oauth_client()
        me = client.get_me()
        my_id = me.data.id
        fans = set()
        resp = client.get_users_followers(my_id, user_auth=True, max_results=1000)
        for u in (resp.data or []):
            fans.add(str(u.id))
        still = []
        for f in data["follows"]:
            if len(unfollowed) >= remaining:
                still.append(f)
                continue
            try:
                old = datetime.fromisoformat(f["at"]) < cutoff
            except Exception:
                old = False
            if (old and f["id"] not in fans
                    and f["handle"].lower() not in never):
                try:
                    client.unfollow_user(f["id"], user_auth=True)
                    data["unfollows"].append({
                        "id": f["id"], "handle": f["handle"],
                        "at": datetime.now(timezone.utc).isoformat(),
                    })
                    unfollowed.append(f["handle"])
                    time.sleep(random.uniform(30, 60))
                    continue
                except Exception:
                    pass
            still.append(f)
        data["follows"] = still
        _save(data)
    except Exception:
        pass
    return unfollowed


# ---------- COMENTARIOS (borradores para Telegram) ----------

def draft_replies(llm, style_prompt: str, limit: int = 2) -> list[dict]:
    """Redacta respuestas a posts recientes con tracción de cuentas del nicho.

    NO publica: devuelve borradores {text, in_reply_to, source_url, handle}
    que main.py envía a Telegram para aprobación.
    """
    from .x_research import fetch_account_posts

    data = _load()
    done = set(data["commented"])
    drafts = []
    for item in fetch_account_posts(limit_per_account=2):
        if len(drafts) >= limit:
            break
        tweet_id = item["url"].rsplit("/", 1)[-1]
        if tweet_id in done or item["score"] < 50:
            continue
        prompt = (
            f"{style_prompt}\n\nPOST DE @{item['source'][2:]}:\n{item['title']}\n\n"
            "Escribe una RESPUESTA a ese post que aporte valor real (matiz, dato, "
            "experiencia o pregunta inteligente). Máximo 200 caracteres, sin repetir "
            "lo que dice el post, sin peloteo. SOLO el texto de la respuesta."
        )
        try:
            text = llm.invoke(prompt).content.strip()
        except Exception:
            continue
        if text and text != "SKIP" and len(text) <= 240:
            drafts.append({
                "type": "reply",
                "text": text,
                "in_reply_to": tweet_id,
                "source_url": item["url"],
                "topic": f"respuesta a {item['source']}",
            })
    return drafts


def mark_commented(tweet_id: str):
    data = _load()
    data["commented"].append(tweet_id)
    data["commented"] = data["commented"][-1000:]
    _save(data)
