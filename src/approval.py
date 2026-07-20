"""Bot de Telegram para aprobación humana de borradores.

Flujo: el agente envía cada borrador con botones ✅ Publicar / ❌ Descartar /
✏️ (el usuario responde citando el mensaje con el texto corregido).
Cada publicación queda registrada en timing para el análisis de horarios.
"""
from __future__ import annotations

import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from . import x_client
from .agent import timing

PENDING: dict[int, dict] = {}  # message_id -> draft
_chat_id = None


def _authorized(update: Update) -> bool:
    return str(update.effective_chat.id) == os.getenv("TELEGRAM_CHAT_ID", "")


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if _authorized(update):
        await update.message.reply_text("🤖 Agente X activo. Te enviaré borradores para aprobar.")


async def send_draft(app: Application, draft: dict):
    chat_id = int(os.environ["TELEGRAM_CHAT_ID"])
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Publicar", callback_data="approve"),
        InlineKeyboardButton("❌ Descartar", callback_data="reject"),
    ]])
    caption = (f"📝 *Borrador* ({len(draft['text'])} caracteres)\n\n{draft['text']}\n\n"
               f"🔗 Fuente: {draft['source_url']}\n"
               "_(responde citando este mensaje para publicar una versión editada)_")
    if draft.get("image"):
        msg = await app.bot.send_photo(
            chat_id=chat_id, photo=open(draft["image"], "rb"),
            caption=caption[:1024], parse_mode="Markdown", reply_markup=kb,
        )
    else:
        msg = await app.bot.send_message(
            chat_id=chat_id, text=caption, parse_mode="Markdown", reply_markup=kb,
        )
    PENDING[msg.message_id] = draft


async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not _authorized(update):
        return
    draft = PENDING.pop(q.message.message_id, None)
    if not draft:
        await q.edit_message_reply_markup(reply_markup=None)
        return
    if q.data == "approve":
        tweet_id = x_client.publish(draft["text"], draft.get("image"))
        timing.record_publish(tweet_id, draft["text"], bool(draft.get("image")))
        await q.edit_message_text(f"✅ Publicado (id: {tweet_id})\n\n{draft['text']}")
    else:
        await q.edit_message_text(f"❌ Descartado\n\n{draft['text']}")


async def on_edit_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Publicar versión editada: responde citando el borrador con tu texto."""
    msg = update.message
    if not _authorized(update) or not msg.reply_to_message:
        return
    orig = PENDING.pop(msg.reply_to_message.message_id, None)
    if orig and msg.text and len(msg.text) <= 280:
        tweet_id = x_client.publish(msg.text, orig.get("image"))
        timing.record_publish(tweet_id, msg.text, bool(orig.get("image")))
        await msg.reply_text(f"✅ Publicada versión editada (id: {tweet_id})")
    elif orig:
        await msg.reply_text("⚠️ Texto vacío o >280 caracteres, no se publicó.")


def build_app() -> Application:
    app = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_edit_reply))
    return app
