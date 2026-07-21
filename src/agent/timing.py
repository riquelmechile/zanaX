"""Timing inteligente: aprende los mejores horarios de publicación.

Flujo:
1. Cada post publicado se registra en DATA_DIR/published.json (id, hora, texto).
2. Un job periódico (metrics) consulta el engagement de esos posts en X.
3. Un LLM analiza ese historial + heurísticas del nicho AI/dev y devuelve las
   mejores horas; el scheduler se reconfigura solo con ellas.

Sin datos suficientes, usa heurísticas razonables del nicho.
"""
from __future__ import annotations

import json
import os
import pathlib
from datetime import datetime, timezone

DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "./data"))
PUBLISHED = DATA_DIR / "published.json"
SCHEDULE = DATA_DIR / "schedule.json"

DEFAULT_HOURS = [9, 18]  # heurística inicial

# Heurísticas del nicho AI/dev (audiencia global, devs revisan X al empezar el
# día, en la comida y al final de la jornada; finde = menos B2B, más side projects)
HEURISTICS = """Heurísticas base para cuentas AI/dev en español/inglés:
- Buenos momentos: 9-10h y 18-19h (Europa), 15-16h (solapa con mañana en EE.UU.).
- Mar-Jue suele rendir mejor que lunes y viernes; domingo bajo.
- Los posts con imagen aguantan mejor horarios secundarios.
"""


def _load(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _save(path: pathlib.Path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def record_publish(tweet_id: str, text: str, had_image: bool):
    """Registra un post publicado para análisis posterior."""
    rows = _load(PUBLISHED, [])
    rows.append({
        "tweet_id": tweet_id,
        "text": text[:120],
        "had_image": had_image,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "metrics": None,
    })
    _save(PUBLISHED, rows[-500:])


def refresh_metrics():
    """Actualiza likes/RTs de los posts registrados (vía X API).

    En FREE_MODE no hace nada: leer métricas cuesta dinero en la API de X.
    """
    from .config import free_mode
    if free_mode():
        return
    bearer = os.getenv("X_BEARER_TOKEN")
    rows = _load(PUBLISHED, [])
    if not bearer or not rows:
        return
    try:
        import tweepy

        client = tweepy.Client(bearer_token=bearer)
        ids = [r["tweet_id"] for r in rows
               if r.get("tweet_id") and r["tweet_id"] != "dry-run"][-100]
        if not ids:
            return
        resp = client.get_tweets(ids, tweet_fields=["public_metrics"])
        metrics = {str(t.id): t.public_metrics for t in (resp.data or [])}
        for r in rows:
            if r.get("tweet_id") in metrics:
                r["metrics"] = metrics[r["tweet_id"]]
        _save(PUBLISHED, rows)
    except Exception:
        return


def analyze_best_hours(llm) -> list[int]:
    """Pide al LLM las 2 mejores horas según historial + heurísticas.

    Devuelve lista de horas (0-23, hora local del servidor) y la persiste.

    En FREE_MODE no hay métricas de X: se usan directamente las horas fijas
    de POST_HOURS (o la heurística inicial), sin llamar al LLM.
    """
    from .config import free_mode
    if free_mode():
        hours = current_hours()
        _save(SCHEDULE, {"hours": hours,
                         "updated_at": datetime.now(timezone.utc).isoformat()})
        return hours
    rows = [r for r in _load(PUBLISHED, []) if r.get("metrics")]
    history = "\n".join(
        f"- {r['published_at']} | imagen={r['had_image']} | "
        f"likes={r['metrics'].get('like_count', 0)} rts={r['metrics'].get('retweet_count', 0)} "
        f"| {r['text'][:60]}"
        for r in rows[-60:]
    ) or "(sin datos de engagement todavía: usa solo heurísticas)"

    prompt = f"""Eres un analista de crecimiento en X para una cuenta de AI/dev.

{HEURISTICS}

HISTORIAL DE ENGAGEMENT PROPIO (UTC):
{history}

TZ del servidor: {os.getenv('TIMEZONE', 'Europe/Madrid')}.
Devuelve las 2 mejores horas del día (0-23, hora local del servidor) para
publicar, separadas por coma. SOLO los números, ej: 9,18"""

    try:
        resp = llm.invoke(prompt).content.strip()
        hours = sorted({int(t) for t in resp.replace(" ", "").split(",")
                        if t.strip().lstrip("-").isdigit() and 0 <= int(t) <= 23})
        if hours:
            _save(SCHEDULE, {"hours": hours[:3],
                             "updated_at": datetime.now(timezone.utc).isoformat()})
            return hours[:3]
    except Exception:
        pass
    return current_hours()


def current_hours() -> list[int]:
    """Horas actualmente configuradas: POST_HOURS (env) > schedule.json > default."""
    raw = os.getenv("POST_HOURS", "")
    hours = sorted({int(h) for h in raw.split(",")
                    if h.strip().isdigit() and 0 <= int(h) <= 23})
    if hours:
        return hours
    return _load(SCHEDULE, {}).get("hours") or DEFAULT_HOURS
