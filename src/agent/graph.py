"""Grafo LangGraph: research -> select -> draft -> image -> approve (Telegram) -> publish."""
from __future__ import annotations

import operator
import os
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from .images import enabled as images_enabled, generate_image
from .style import SYSTEM_PROMPT
from .tools import gather_trends, web_search


class AgentState(TypedDict, total=False):
    trends: list[dict]
    candidates: Annotated[list[dict], operator.add]
    drafts: list[dict]
    error: str


_llm = None

def llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(model=os.getenv("LLM_MODEL", "gpt-4o-mini"), temperature=0.8)
    return _llm


# ---------- NODOS ----------

def research_node(state: AgentState) -> AgentState:
    """Recolecta tendencias de HN, GitHub y Reddit."""
    trends = gather_trends()
    return {"trends": trends}


def select_node(state: AgentState) -> AgentState:
    """El LLM puntúa y elige las N mejores tendencias para AI/dev."""
    trends = state.get("trends", [])
    if not trends:
        return {"candidates": []}
    n = int(os.getenv("POSTS_PER_DAY", "2"))
    listing = "\n".join(f"{i}. [{t['source']}] {t['title']}" for i, t in enumerate(trends))
    prompt = (
        "De estas tendencias, elige las "
        f"{n} más interesantes para una cuenta de X sobre AI y desarrollo de software. "
        "Responde SOLO con los números separados por comas.\n\n" + listing
    )
    resp = llm().invoke(prompt).content.strip()
    picks = []
    for tok in resp.replace(" ", "").split(","):
        if tok.isdigit() and int(tok) < len(trends):
            picks.append(trends[int(tok)])
    return {"candidates": picks[:n]}


def draft_node(state: AgentState) -> AgentState:
    """Genera un borrador con voz propia por cada candidato, con contexto web."""
    drafts = []
    for c in state.get("candidates", []):
        context = web_search(c["title"], limit=3)
        ctx = "\n".join(f"- {x['title']}: {x.get('snippet', '')[:200]}" for x in context)
        prompt = (
            f"{SYSTEM_PROMPT}\n\nTENDENCIA: {c['title']}\nURL: {c['url']}\n"
            f"CONTEXTO ADICIONAL:\n{ctx}\n\nEscribe el post:"
        )
        text = llm().invoke(prompt).content.strip()
        if text and text != "SKIP" and len(text) <= 280:
            drafts.append({"text": text, "source_url": c["url"], "topic": c["title"]})
    return {"drafts": drafts}


def image_node(state: AgentState) -> AgentState:
    """Genera una imagen opcional por borrador (nano banana / Gemini image)."""
    if not images_enabled():
        return {}
    for d in state.get("drafts", []):
        prompt_resp = llm().invoke(
            "Escribe un prompt corto EN INGLÉS para generar una imagen que acompañe "
            "este post de X sobre tecnología/AI. Estilo: minimalista, editorial, sin texto "
            "en la imagen. Devuelve SOLO el prompt.\n\nPOST: " + d["text"]
        ).content.strip()
        path = generate_image(prompt_resp)
        if path:
            d["image"] = path
    return {"drafts": state.get("drafts", [])}


# ---------- GRAFO ----------

def build_graph():
    """Grafo automático hasta el borrador. La aprobación/publicación es
    asíncrona (Telegram), por lo que vive fuera del grafo: el flujo es
    research -> select -> draft -> image -> END, y el scheduler envía los
    borradores al bot de Telegram, que publica al recibir ✅."""
    g = StateGraph(AgentState)
    g.add_node("research", research_node)
    g.add_node("select", select_node)
    g.add_node("draft", draft_node)
    g.add_node("image", image_node)
    g.set_entry_point("research")
    g.add_edge("research", "select")
    g.add_edge("select", "draft")
    g.add_edge("draft", "image")
    g.add_edge("image", END)
    return g.compile()


graph = build_graph()
