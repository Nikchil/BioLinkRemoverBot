# User Command Callback Handlers

from bot.bot import app
from pyrogram import filters
from pyrogram.types import CallbackQuery
from utils.language import get_message
from database.user_language import get_user_language

@app.on_callback_query(filters.regex("help_warn"))
async def help_warn_cb(client, query: CallbackQuery):
    lang = get_user_language(query.from_user.id)
    await query.message.edit_text(get_message(lang, "help_warn"))
