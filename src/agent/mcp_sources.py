"""Fuentes adicionales vía MCP (Model Context Protocol).

Estándar 2026: en vez de hardcodear integraciones, el agente se conecta a
servidores MCP (arXiv, Product Hunt, YouTube...) definidos en MCP_SERVERS.

Config (env):
  MCP_SERVERS='[{"name":"arxiv","url":"https://mcp.example.com/arxiv/mcp"}]'

Cada servidor debe exponer tools tipo búsqueda (search_*, *trending*, latest*).
Si MCP_SERVERS está vacío o langchain-mcp-adapters no está instalado, el módulo
devuelve [] y el agente sigue con las fuentes clásicas. Fail-safe total.
"""
from __future__ import annotations

import asyncio
import json
import os


def configured() -> list[dict]:
    try:
        return json.loads(os.getenv("MCP_SERVERS", "[]"))
    except Exception:
        return []


async def _fetch_from_server(server: dict, limit: int) -> list[dict]:
    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient({
        server["name"]: {"url": server["url"], "transport": "streamable_http"}
    })
    tools = await client.get_tools()
    items = []
    for tool in tools:
        name = tool.name.lower()
        # heurística: tools de búsqueda/tendencias sin argumentos obligatorios
        if not any(k in name for k in ("search", "trending", "latest", "top", "hot")):
            continue
        try:
            args = {}
            schema = tool.args or {}
            if "query" in schema:
                args["query"] = "AI agents LLM"
            if "limit" in schema:
                args["limit"] = limit
            if "max_results" in schema:
                args["max_results"] = limit
            result = await tool.ainvoke(args)
            text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            # cada resultado se trocea en líneas tipo "título - url"
            for line in text.splitlines()[:limit]:
                line = line.strip("- •")
                if len(line) > 15:
                    items.append({
                        "source": f"mcp/{server['name']}",
                        "title": line[:200],
                        "url": server["url"],
                        "score": 0,
                    })
        except Exception:
            continue
    return items


def fetch_mcp_trends(limit_per_server: int = 5) -> list[dict]:
    """Tendencias de todos los servidores MCP configurados. Fail-safe → []."""
    servers = configured()
    if not servers:
        return []
    try:
        items = []
        for s in servers:
            try:
                items.extend(asyncio.run(_fetch_from_server(s, limit_per_server)))
            except RuntimeError:
                # ya hay un loop corriendo (raro en el worker thread): saltar
                continue
            except Exception:
                continue
        return items
    except Exception:
        return []
