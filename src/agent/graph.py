"""Grafo LangGraph: research -> select -> image -> draft -> critic -> approve -> publish.

Inteligencia 2026:
- select y draft usan MEMORIA de contenido (anti-repetición + learnings reales)
- critic: crítica grounded (rúbrica + top posts históricos) con modelo distinto
  al que redactó; si la nota < umbral, reescribe (máx. N iteraciones)
- research incluye fuentes MCP opcionales (arXiv, Product Hunt...)

El flujo automático termina en `critic`; la aprobación (Telegram) y la
publicación (X) son asíncronas y viven fuera del grafo.
"""
from __future__ import annotations

import operator
import os
from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph

from . import memory
from .critic import critique, revise
from .images import enabled as images_enabled, generate_image
from .llm import get_llm
from .mcp_sources import fetch_mcp_trends
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
    """Recolecta tendencias de HN, GitHub, Reddit, X y servidores MCP."""
    trends = gather_trends() + fetch_account_posts() + fetch_mcp_trends()
    return {"trends": trends}


def select_node(state: AgentState) -> AgentState:
    """El LLM elige las N mejores tendencias; la memoria filtra repetidos."""
    trends = state.get("trends", [])
    if not trends:
        return {"candidates": []}
    # anti-repetición: descarta temas ya cubiertos antes de preguntar al LLM
    fresh = [t for t in trends if not memory.already_covered(t["title"])]
    pool = fresh or trends  # si TODO está cubierto, al menos no romper el ciclo
    n = int(os.getenv("POSTS_PER_DAY", "2"))
    listing = "\n".join(f"{i}. [{t['source']}] {t['title']}" for i, t in enumerate(pool))
    prompt = (
        "Eres el editor de una cuenta de X sobre AI y desarrollo. De estas "
        f"tendencias elige las {n} con más potencial de conversación para devs "
        "(novedad real, utilidad práctica o debate sano; evita spam de producto). "
        "Responde SOLO con los números separados por comas.\n\n" + listing
    )
    resp = llm().invoke(prompt).content.strip()
    picks = []
    for tok in resp.replace(" ", "").split(","):
        if tok.isdigit() and int(tok) < len(pool):
            picks.append(pool[int(tok)])
    return {"candidates": picks[:n]}


def image_node(state: AgentState) -> AgentState:
    """Crea imagen (nano banana) ANTES de redactar, solo en una fracción.

    IMAGE_RATIO (0.0-1.0, def. 0.5): proporción de posts con imagen.
    Cada imagen cuesta ~$0.039 — el ratio controla el coste mensual.
    """
    if not images_enabled():
        return {"candidates": state.get("candidates", [])}
    ratio = float(os.getenv("IMAGE_RATIO", "0.5"))
    candidates = state.get("candidates", [])
    n_images = max(1, round(len(candidates) * ratio)) if candidates else 0
    for c in candidates[:n_images]:
        prompt_resp = llm().invoke(
            "Escribe un prompt corto EN INGLÉS para generar una imagen editorial "
            "minimalista (sin texto en la imagen) que represente esta noticia de "
            "tecnología/AI. Devuelve SOLO el prompt.\n\nNOTICIA: " + c["title"]
        ).content.strip()
        path = generate_image(prompt_resp)
        if path:
            c["image"] = path
    return {"candidates": candidates}


def draft_node(state: AgentState) -> AgentState:
    """Redacta con voz propia + aprendizajes reales de la audiencia."""
    drafts = []
    learnings = memory.learning_context()
    for c in state.get("candidates", []):
        context = web_search(c["title"], limit=3)
        ctx = "\n".join(f"- {x['title']}: {x.get('snippet', '')[:200]}" for x in context)
        has_img = "SÍ" if c.get("image") else "NO"
        prompt = (
            f"{SYSTEM_PROMPT}\n\n{learnings}\n\n"
            f"TENDENCIA: {c['title']}\nURL: {c['url']}\n"
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


def critic_node(state: AgentState) -> AgentState:
    """Crítica grounded: puntúa contra rúbrica + top posts reales y reescribe.

    El crítico usa el rol 'cheap' (modelo distinto al de redacción) para
    romper puntos ciegos. Máx. CRITIC_MAX_RETRIES iteraciones por borrador.
    """
    threshold = float(os.getenv("CRITIC_THRESHOLD", "0.8"))
    max_retries = int(os.getenv("CRITIC_MAX_RETRIES", "2"))
    learnings = memory.learning_context()
    for d in state.get("drafts", []):
        for attempt in range(max_retries):
            result = critique(llm(), d["text"], d["topic"], learnings)
            d["critic_score"] = result["score"]
            if result["score"] >= threshold or not result["feedback"]:
                break
            d["text"] = revise(llm("draft"), d["text"], result["feedback"],
                               d["topic"], SYSTEM_PROMPT, bool(d.get("image")))
    return {"drafts": state.get("drafts", [])}


# ---------- GRAFO ----------

def build_graph():
    """research -> select -> image -> draft -> critic -> END."""
    g = StateGraph(AgentState)
    g.add_node("research", research_node)
    g.add_node("select", select_node)
    g.add_node("image", image_node)
    g.add_node("draft", draft_node)
    g.add_node("critic", critic_node)
    g.set_entry_point("research")
    g.add_edge("research", "select")
    g.add_edge("select", "image")
    g.add_edge("image", "draft")
    g.add_edge("draft", "critic")
    g.add_edge("critic", END)
    return g.compile()


graph = build_graph()
