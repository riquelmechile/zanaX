"""Config global: modo gratis (FREE_MODE) y helpers de entorno.

FREE_MODE=true (default) elimina TODA lectura de la API de X (lo más caro del
pay-per-use 2026) y usa solo recursos gratuitos:
- Research: HN, GitHub Trending, Reddit, DuckDuckGo (gratis, sin key)
- LLM: Gemini capa gratis de AI Studio (Flash para todo)
- Imágenes: cuota gratis de AI Studio (si se agota, el post sale sin imagen)
- Timing: horas fijas por POST_HOURS (sin métricas de X)
- Respuestas del nicho: desactivadas (requieren leer X)

Publicar sigue siendo gratis con la capa Free de la API de X (~500 posts/mes).
"""
from __future__ import annotations

import os


def free_mode() -> bool:
    """True si estamos en modo gratis (sin lecturas de la API de X)."""
    return os.getenv("FREE_MODE", "true").lower() in ("1", "true", "yes")
