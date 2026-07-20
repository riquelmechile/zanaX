"""Factory de LLMs multi-provider.

Dos roles:
- cheap: tareas de análisis/selección (select, prompts de imagen, timing, growth)
- draft: redacción del post y comentarios (aquí se nota la calidad de voz)

Provider por defecto: Google Gemini (rápido, barato, multimodal y reutiliza la
GOOGLE_API_KEY de nano banana). Conmutable con LLM_PROVIDER=openai|anthropic.
"""
from __future__ import annotations

import os

_cache: dict[str, object] = {}


def get_llm(role: str = "cheap"):
    """Devuelve el LLM para el rol ('cheap' | 'draft'), cacheado."""
    if role in _cache:
        return _cache[role]

    provider = os.getenv("LLM_PROVIDER", "google").lower()
    if role == "draft":
        model = os.getenv("LLM_MODEL_DRAFT", "gemini-2.5-pro")
        temperature = 0.8
    else:
        model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        temperature = 0.3

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model=model, temperature=temperature,
            google_api_key=os.environ["GOOGLE_API_KEY"],
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=model, temperature=temperature,
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=model, temperature=temperature,
            api_key=os.environ["OPENAI_API_KEY"],
        )
    else:
        raise ValueError(f"LLM_PROVIDER desconocido: {provider}")

    _cache[role] = llm
    return llm
