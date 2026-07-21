"""Memoria de contenido a largo plazo (estilo Reflexion).

Qué guarda (DATA_DIR/memory.json):
- posts: tema, ángulo/gancho usado, texto, tweet_id, fecha → anti-repetición
- learnings: lecciones extraídas periódicamente por el LLM ("qué tipo de
  posts rinden más en ESTA cuenta") cruzando engagement con temas/estilos

Quién la usa:
- select_node: filtra candidatos cuyo tema ya se cubrió (anti-repetición)
- draft_node: recibe los learnings y los mejores posts históricos (grounded)
- approval: registra cada publicación
"""
from __future__ import annotations

import json
import os
import pathlib
import re
from datetime import datetime, timezone

DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "./data"))
MEMORY = DATA_DIR / "memory.json"
PUBLISHED = DATA_DIR / "published.json"


def _load(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _save(path: pathlib.Path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def enabled() -> bool:
    return os.getenv("MEMORY_ENABLED", "true").lower() == "true"


# ---------- ESCRITURA ----------

def record_post(topic: str, text: str, tweet_id: str):
    """Registra tema y ángulo de cada post publicado (anti-repetición)."""
    if not enabled():
        return
    mem = _load(MEMORY, {"posts": [], "learnings": []})
    mem["posts"].append({
        "topic": topic[:200],
        "hook": text[:100],
        "tweet_id": tweet_id,
        "at": datetime.now(timezone.utc).isoformat(),
    })
    mem["posts"] = mem["posts"][-1000:]
    _save(MEMORY, mem)


def update_learnings(llm) -> list[str]:
    """Job semanal: el LLM extrae lecciones de los posts con más engagement.

    Cruza memory.posts con published.json (métricas) y genera 3-5 lecciones
    accionables que se inyectan en los prompts de redacción.
    """
    if not enabled():
        return []
    mem = _load(MEMORY, {"posts": [], "learnings": []})
    published = {r["tweet_id"]: r for r in _load(PUBLISHED, []) if r.get("metrics")}
    rows = []
    for p in mem["posts"]:
        pub = published.get(p.get("tweet_id"))
        if pub:
            m = pub["metrics"]
            rows.append({
                "topic": p["topic"], "hook": p["hook"],
                "likes": m.get("like_count", 0), "rts": m.get("retweet_count", 0),
                "had_image": pub.get("had_image"),
            })
    if len(rows) < 5:  # aún no hay datos suficientes
        return mem.get("learnings", [])
    rows.sort(key=lambda r: -(r["likes"] + 3 * r["rts"]))
    sample = "\n".join(
        f"- [{r['likes']}❤ {r['rts']}🔁 img={r['had_image']}] {r['topic']} → gancho: {r['hook']}"
        for r in rows[:10] + rows[-5:]
    )
    prompt = (
        "Eres el analista de una cuenta de X sobre AI/dev. Estos son sus posts con "
        "MÁS y MENOS engagement. Extrae 3-5 lecciones concretas y accionables sobre "
        "QUÉ temas, ganchos o formatos rinden más (ej: 'las preguntas directas rinden "
        "el doble', 'posts con imagen + hot take funcionan'). Una por línea, sin números.\n\n"
        + sample
    )
    try:
        resp = llm.invoke(prompt).content.strip()
        learnings = [l.strip("- •") for l in resp.splitlines() if l.strip()][:5]
        if learnings:
            mem["learnings"] = learnings
            mem["learnings_at"] = datetime.now(timezone.utc).isoformat()
            _save(MEMORY, mem)
    except Exception:
        pass
    return mem.get("learnings", [])


# ---------- LECTURA ----------

_STOPWORDS = {"the", "a", "an", "de", "la", "el", "en", "y", "is", "to", "of",
              "for", "on", "with", "new", "how", "why", "what", "los", "las"}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-záéíóúñ0-9]+", text.lower())
            if len(t) > 3 and t not in _STOPWORDS}


def already_covered(title: str, threshold: float = 0.5) -> bool:
    """True si el tema se parece demasiado a algo ya publicado (Jaccard)."""
    if not enabled():
        return False
    mem = _load(MEMORY, {"posts": []})
    t = _tokens(title)
    if not t:
        return False
    for p in mem["posts"][-150:]:
        pt = _tokens(p["topic"])
        if pt and len(t & pt) / len(t | pt) >= threshold:
            return True
    return False


def learning_context() -> str:
    """Bloque de texto con aprendizajes para inyectar en prompts (grounded)."""
    if not enabled():
        return ""
    mem = _load(MEMORY, {"posts": [], "learnings": []})
    parts = []
    if mem.get("learnings"):
        parts.append("LECCIONES DE TU PROPIA AUDIENCIA (aprendidas de engagement real):\n"
                     + "\n".join(f"- {l}" for l in mem["learnings"]))
    covered = [p["topic"] for p in mem["posts"][-30:]]
    if covered:
        parts.append("TEMAS YA CUBIERTOS recientemente (NO los repitas ni uses el mismo ángulo):\n"
                     + "\n".join(f"- {c}" for c in covered))
    return "\n\n".join(parts)
