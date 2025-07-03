from pyrogram import filters
from pyrogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from config import LOG_CHANNEL, OWNER_ID
from database.core import is_whitelisted, increment_violations, remove_user_record
from database.config import get_config
from utils.filters import contains_link


def init(app):
    @app.on_message(filters.group & filters.text)
    async def check_user_identity(_, message: Message):
        user = message.from_user
        chat_id = message.chat.id

        if not user or user.is_bot:
            return

        user_id = user.id

        try:
            # Skip if OWNER
            if user_id == OWNER_ID:
                await app.send_message(
                    LOG_CHANNEL,
                    f"👑 Skipped moderation for bot owner: <a href='tg://user?id={user_id}'>{user.first_name}</a>"
                )
                remove_user_record(user_id)
                return

            # Check member status (admin/creator)
            member = await app.get_chat_member(chat_id, user_id)

            await app.send_message(
                LOG_CHANNEL,
                f"👥 Member status check:\n"
                f"👤 <a href='tg://user?id={user_id}'>{user.first_name}</a>\n"
                f"📌 Status: <b>{member.status}</b>"
            )

            if member.status in ("administrator", "creator"):
                remove_user_record(user_id)
                await app.send_message(
                    LOG_CHANNEL,
                    f"✅ Skipped scan and cleared violations for admin: <a href='tg://user?id={user_id}'>{user.first_name}</a>"
                )
                return

        except Exception as e:
            print(f"[!] Failed to get member status: {e}")
            return

        # Skip if whitelisted
        if is_whitelisted(user_id):
            return

        try:
            identity_text = user.username or ""

            # Check bio
            try:
                user_chat = await app.get_chat(user_id)
                if hasattr(user_chat, "bio") and user_chat.bio:
                    identity_text += f" {user_chat.bio}"
            except Exception as e:
                print(f"[!] Failed to get bio: {e}")

            # If any link or @username is detected
            if contains_link(identity_text):
                await message.delete()
                count = increment_violations(user_id)
                config = get_config(chat_id)
                limit = config['warn_limit']
                mode = config['punishment_mode']

                # Log violation
                await app.send_message(
                    LOG_CHANNEL,
                    f"🚨 <b>Violation Detected</b>\n"
                    f"👤 <a href='tg://user?id={user_id}'>{user.first_name}</a> [<code>{user_id}</code>]\n"
                    f"🔗 <b>Bio/Username:</b> <code>{identity_text.strip()}</code>\n"
                    f"⚠️ <b>Warnings:</b> {count}/{limit}\n"
                    f"🗨 <b>Chat:</b> <code>{chat_id}</code>\n"
                    f"📝 <b>Message:</b> <code>{message.text[:100]}</code>"
                )

                # Take action if limit exceeded
                if count >= limit:
                    if mode == "mute":
                        await message.chat.restrict_member(user_id, ChatPermissions(can_send_messages=False))
                    elif mode == "ban":
                        await message.chat.ban_member(user_id)

                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔓 Unmute User", callback_data=f"unmute:{user_id}")]
                    ])

                    await message.reply(
                        f"🚫 <b>User Muted for Repeated Violations</b>\n"
                        f"👤 <a href='tg://user?id={user_id}'>{user.first_name}</a>\n"
                        f"⚠️ <b>Total Violations:</b> {count} / {limit}\n"
                        f"📛 <b>Reason:</b> Suspicious username or bio link detected.\n"
                        f"🔒 <b>Action Taken:</b> Muted in this group.",
                        reply_markup=keyboard,
                        quote=True
                    )
                else:
                    await message.reply(
                        f"⚠️ <b>Warning Issued</b>\n"
                        f"👤 <a href='tg://user?id={user_id}'>{user.first_name}</a>\n"
                        f"⚠️ <b>Violation:</b> Detected link or @username in profile.\n"
                        f"📌 <b>Warning Count:</b> {count} / {limit}\n"
                        f"🛑 Please remove links from your profile to avoid restrictions.",
                        quote=True
                    )

        except Exception as e:
            print(f"[!] Identity check failed for user {user_id}: {e}")
