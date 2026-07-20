"""Entrypoint: scheduler diario + bot de Telegram (polling) en un solo proceso.

Despliegue: un solo servicio en Railway / VPS / cualquier runner Python.
"""
from __future__ import annotations

import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from src.agent.graph import graph
from src.approval import build_app, send_draft

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("x-ai-agent")


async def run_agent(app):
    """Ejecuta el grafo y manda los borradores a Telegram."""
    log.info("Ejecutando ciclo del agente...")
    try:
        result = await asyncio.to_thread(graph.invoke, {"candidates": [], "drafts": []})
        drafts = result.get("drafts", [])
        log.info("Generados %d borradores", len(drafts))
        for d in drafts:
            await send_draft(app, d)
        if not drafts:
            log.info("Sin borradores válidos en este ciclo.")
    except Exception:
        log.exception("Error en el ciclo del agente")


async def main():
    app = build_app()
    scheduler = AsyncIOScheduler(timezone=os.getenv("TIMEZONE", "Europe/Madrid"))
    # Dos ventanas de publicación: mañana y tarde (ajusta a tu audiencia)
    scheduler.add_job(run_agent, CronTrigger(hour=9, minute=30), args=[app])
    scheduler.add_job(run_agent, CronTrigger(hour=18, minute=0), args=[app])
    scheduler.start()

    async with app:
        await app.start()
        await app.updater.start_polling()
        log.info("Bot de Telegram escuchando. Scheduler activo (DRY_RUN=%s).",
                 os.getenv("DRY_RUN", "true"))
        # Ejecuta un ciclo al arrancar para probar el pipeline
        await run_agent(app)
        # Mantener vivo
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
