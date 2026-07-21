"""Crecimiento en X: SOLO borradores de respuestas a posts del nicho.

El follow/unfollow automático se eliminó (coste API + riesgo de patrón):
se hace a mano desde la app de X. Lo que queda aquí:

- Comentarios: el agente redacta respuestas con tu voz a posts con tracción
  y las manda a Telegram; solo se publican si las apruebas (✅).
  En FREE_MODE quedan desactivadas (requieren leer X).

Requiere X_BEARER_TOKEN (lectura) y FREE_MODE=false.
"""
from __future__ import annotations

import json
import os
import pathlib

DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "./data"))
GROWTH = DATA_DIR / "growth.json"


def _load() -> dict:
    try:
        return json.loads(GROWTH.read_text())
    except Exception:
        return {"commented": []}


def _save(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GROWTH.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def draft_replies(llm, style_prompt: str, limit: int = 2) -> list[dict]:
    """Redacta respuestas a posts recientes con tracción de cuentas del nicho.

    NO publica: devuelve borradores {text, in_reply_to, source_url}
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
