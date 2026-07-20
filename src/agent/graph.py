"""Grafo LangGraph proactivo: research -> select -> image -> draft -> approve -> publish.

El flujo automático termina en `draft`; la aprobación (Telegram) y la
publicación (X) son asíncronas y viven fuera del grafo.
"""
from __future__ import annotations

import operator
import os
from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph

from .images import enabled as images_enabled, generate_image
from .llm import get_llm
from .style import SYSTEM_PROMPT
from .tools import gather_trends, web_search
from .x_research import fetch_account_posts


class AgentState(TypedDict, total=False):
    trends: list[dict]
    candidates: Annotated[list[dict], operator.add]
    drafts: list[dict]
    error: str


def llm(role: str = "cheap"):
    """Compat: devuelve el LLM del rol ('cheap' | 'draft')."""
    return get_llm(role)


# ---------- NODOS ----------

def research_node(state: AgentState) -> AgentState:
    """Recolecta tendencias de HN, GitHub, Reddit y de cuentas clave en X."""
    trends = gather_trends() + fetch_account_posts()
    return {"trends": trends}


def select_node(state: AgentState) -> AgentState:
    """El LLM analiza y elige las N mejores tendencias para AI/dev.

    Prioriza lo que genera conversación (novedad, controversia sana,
    utilidad práctica para devs) y evita repetir fuentes.
    """
    trends = state.get("trends", [])
    if not trends:
        return {"candidates": []}
    n = int(os.getenv("POSTS_PER_DAY", "2"))
    listing = "\n".join(f"{i}. [{t['source']}] {t['title']}" for i, t in enumerate(trends))
    prompt = (
        "Eres el editor de una cuenta de X sobre AI y desarrollo. De estas "
        f"tendencias elige las {n} con más potencial de conversación para devs "
        "(novedad real, utilidad práctica o debate sano; evita spam de producto). "
        "Responde SOLO con los números separados por comas.\n\n" + listing
    )
    resp = llm().invoke(prompt).content.strip()
    picks = []
    for tok in resp.replace(" ", "").split(","):
        if tok.isdigit() and int(tok) < len(trends):
            picks.append(trends[int(tok)])
    return {"candidates": picks[:n]}


def image_node(state: AgentState) -> AgentState:
    """Crea la imagen de cada candidato (nano banana) ANTES de redactar.

    El prompt visual sale del tema, no del texto, para que el post se escriba
    después pensando en acompañar esa imagen.
    """
    if not images_enabled():
        return {"candidates": state.get("candidates", [])}
    for c in state.get("candidates", []):
        prompt_resp = llm().invoke(
            "Escribe un prompt corto EN INGLÉS para generar una imagen editorial "
            "minimalista (sin texto en la imagen) que represente esta noticia de "
            "tecnología/AI. Devuelve SOLO el prompt.\n\nNOTICIA: " + c["title"]
        ).content.strip()
        path = generate_image(prompt_resp)
        if path:
            c["image"] = path
    return {"candidates": state.get("candidates", [])}


def draft_node(state: AgentState) -> AgentState:
    """Redacta el post con voz propia, ya sabiendo si lleva imagen."""
    drafts = []
    for c in state.get("candidates", []):
        context = web_search(c["title"], limit=3)
        ctx = "\n".join(f"- {x['title']}: {x.get('snippet', '')[:200]}" for x in context)
        has_img = "SÍ" if c.get("image") else "NO"
        prompt = (
            f"{SYSTEM_PROMPT}\n\nTENDENCIA: {c['title']}\nURL: {c['url']}\n"
            f"CONTEXTO ADICIONAL:\n{ctx}\n"
            f"EL POST LLEVA IMAGEN ADJUNTA: {has_img} (si lleva, el texto puede "
            "ser más corto porque la imagen comunica parte del mensaje).\n\n"
            "Escribe el post:"
        )
        text = llm("draft").invoke(prompt).content.strip()
        if text and text != "SKIP" and len(text) <= 280:
            drafts.append({
                "type": "post",
                "text": text,
                "source_url": c["url"],
                "topic": c["title"],
                "image": c.get("image"),
            })
    return {"drafts": drafts}


# ---------- GRAFO ----------

def build_graph():
    """research -> select -> image -> draft -> END. El scheduler envía los
    borradores a Telegram y, al aprobar, se publican en X."""
    g = StateGraph(AgentState)
    g.add_node("research", research_node)
    g.add_node("select", select_node)
    g.add_node("image", image_node)
    g.add_node("draft", draft_node)
    g.set_entry_point("research")
    g.add_edge("research", "select")
    g.add_edge("select", "image")
    g.add_edge("image", "draft")
    g.add_edge("draft", END)
    return g.compile()


graph = build_graph()
