"""Entrypoint: scheduler dinámico + bot de Telegram (polling) en un proceso.

El scheduler NO es fijo: usa las horas que el módulo de timing ha aprendido
(LLM + engagement propio) y se reconfigura cada semana. Un job diario refresca
métricas de los posts publicados para alimentar ese análisis.
"""
from __future__ import annotations

import asyncio
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from src.agent.graph import graph, llm
from src.agent import growth, memory, timing
from src.agent.style import SYSTEM_PROMPT
from src.approval import build_app, send_draft

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("zanax")


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
        # Comentarios proactivos: borradores de respuestas a posts del nicho
        replies = await asyncio.to_thread(growth.draft_replies, llm("draft"), SYSTEM_PROMPT)
        for r in replies:
            await send_draft(app, r)
    except Exception:
        log.exception("Error en el ciclo del agente")


def schedule_posts(scheduler: AsyncIOScheduler, app):
    """(Re)programa los ciclos del agente según las mejores horas aprendidas."""
    scheduler.remove_all_jobs()
    for i, hour in enumerate(timing.current_hours()):
        scheduler.add_job(run_agent, CronTrigger(hour=hour, minute=30 if i == 0 else 0),
                          args=[app], id=f"post_{hour}")
    log.info("Ciclos programados a las horas: %s", timing.current_hours())
    # Job diario: refresca métricas de engagement
    scheduler.add_job(lambda: timing.refresh_metrics(), CronTrigger(hour=7),
                      id="metrics")
    # Job semanal (lunes): el LLM re-analiza horarios y extrae aprendizajes
    def retrain():
        hours = timing.analyze_best_hours(llm())
        log.info("Timing actualizado por LLM: %s", hours)
        learnings = memory.update_learnings(llm())
        log.info("Learnings actualizados: %s", learnings)
        schedule_posts(scheduler, app)
    scheduler.add_job(retrain, CronTrigger(day_of_week="mon", hour=8), id="retrain")


async def main():
    app = build_app()
    scheduler = AsyncIOScheduler(timezone=os.getenv("TIMEZONE", "Europe/Madrid"))
    schedule_posts(scheduler, app)
    scheduler.start()

    async with app:
        await app.start()
        await app.updater.start_polling()
        log.info("Bot de Telegram escuchando. Scheduler activo (DRY_RUN=%s).",
                 os.getenv("DRY_RUN", "true"))
        await run_agent(app)  # ciclo de prueba al arrancar
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
