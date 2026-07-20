"""Crítico grounded: puntúa cada borrador contra rúbrica + datos reales.

Principio 2026: la autocrítica a secas falla (el modelo se aprueba solo).
Aquí la crítica es GROUNDED:
1. Rúbrica fija (voz, gancho, valor, claridad, reglas de X)
2. Los mejores posts históricos de la cuenta como referencia (engagement real)
3. Modelo DISTINTO al que redactó (rol cheap/Flash critica al rol draft/Pro)

Si la nota < CRITIC_THRESHOLD, devuelve feedback y el grafo reescribe
(máx. CRITIC_MAX_RETRIES iteraciones).
"""
from __future__ import annotations

import json
import os
import pathlib

DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "/tmp/zanax-data"))
PUBLISHED = DATA_DIR / "published.json"

RUBRIC = """RÚBRICA (0.0 a 1.0 cada criterio):
- hook: ¿los primeros 80 caracteres detienen el scroll?
- value: ¿aporta opinión, dato o ángulo que no está en la noticia original?
- voice: ¿suena a dev real con criterio y no a marca corporativa ni a IA?
- clarity: ¿se entiende sin contexto externo? ¿una idea por post?
- rules: ≤280 caracteres, 0-1 emojis, sin copiar frases del original"""


def _top_posts(n: int = 5) -> list[str]:
    """Los N posts con más engagement de la cuenta (referencia grounded)."""
    try:
        rows = json.loads(PUBLISHED.read_text())
    except Exception:
        return []
    scored = [
        (r["metrics"].get("like_count", 0) + 3 * r["metrics"].get("retweet_count", 0), r["text"])
        for r in rows if r.get("metrics")
    ]
    scored.sort(key=lambda x: -x[0])
    return [t for s, t in scored[:n] if s > 0]


def critique(llm, draft_text: str, topic: str, learnings: str = "") -> dict:
    """Puntúa un borrador. Devuelve {score: float, feedback: str}."""
    threshold = float(os.getenv("CRITIC_THRESHOLD", "0.8"))
    top = _top_posts()
    top_block = ""
    if top:
        top_block = ("POSTS QUE MEJOR RINDIERON EN ESTA CUENTA (referencia de calidad):\n"
                     + "\n".join(f"- {t}" for t in top) + "\n\n")
    prompt = f"""Eres un editor jefe durísimo de una cuenta de X sobre AI/dev.

{RUBRIC}

{top_block}{learnings}

TEMA: {topic}
BORRADOR A EVALUAR:
{draft_text}

Responde SOLO con JSON válido:
{{"score": <0.0-1.0 promedio de los 5 criterios>, "feedback": "<si score < {threshold}: una instrucción concreta y corta para mejorarlo; si no: ''>"}}"""
    try:
        resp = llm.invoke(prompt).content.strip()
        # extrae el JSON aunque venga con ```json
        start, end = resp.find("{"), resp.rfind("}") + 1
        data = json.loads(resp[start:end])
        return {"score": float(data.get("score", 0)), "feedback": str(data.get("feedback", ""))}
    except Exception:
        return {"score": 1.0, "feedback": ""}  # fail-open: no bloquear el pipeline


def revise(llm_draft, draft_text: str, feedback: str, topic: str,
           style_prompt: str, has_image: bool) -> str:
    """Reescribe el borrador aplicando el feedback del crítico."""
    has_img = "SÍ" if has_image else "NO"
    prompt = (
        f"{style_prompt}\n\nTEMA: {topic}\n"
        f"BORRADOR ACTUAL:\n{draft_text}\n\n"
        f"FEEDBACK DEL EDITOR (aplícalo sin perder tu voz): {feedback}\n"
        f"EL POST LLEVA IMAGEN ADJUNTA: {has_img}\n\n"
        "Reescribe el post. SOLO el texto final:"
    )
    try:
        text = llm_draft.invoke(prompt).content.strip()
        if text and len(text) <= 280:
            return text
    except Exception:
        pass
    return draft_text
