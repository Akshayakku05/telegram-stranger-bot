import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------- TOKEN ----------------
#from dotenv import load_dotenv
#load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


# ---------------- DATA ----------------
waiting_users = []
active_chats = {}

# ---------------- KEYBOARDS ----------------
def get_idle_keyboard():
    return ReplyKeyboardMarkup(
        [["🔍 Find Stranger"]],
        resize_keyboard=True
    )

def get_chat_keyboard():
    return ReplyKeyboardMarkup(
        [["⏭ Next", "🛑 Stop"]],
        resize_keyboard=True
    )

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Stranger Chat!\n\nClick below to start.",
        reply_markup=get_idle_keyboard()
    )

# ---------------- FIND STRANGER ----------------
async def find_stranger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in active_chats:
        await update.message.reply_text(
            "⚠️ You're already chatting.",
            reply_markup=get_chat_keyboard()
        )
        return

    if user_id in waiting_users:
        await update.message.reply_text("⏳ Still waiting for a partner...")
        return

    if waiting_users:
        partner = waiting_users.pop(0)

        while partner in active_chats:
            if not waiting_users:
                break
            partner = waiting_users.pop(0)

        if partner != user_id:
            active_chats[user_id] = partner
            active_chats[partner] = user_id

            try:
                await context.bot.send_message(
                    user_id,
                    "✅ Connected! Say hi 👋",
                    reply_markup=get_chat_keyboard()
                )
                await context.bot.send_message(
                    partner,
                    "✅ Connected! Say hi 👋",
                    reply_markup=get_chat_keyboard()
                )
            except:
                cleanup(user_id)
                cleanup(partner)
        else:
            waiting_users.append(user_id)
            await update.message.reply_text("⏳ Waiting for a stranger...")
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("⏳ Waiting for a stranger...")

# ---------------- NEXT ----------------
async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in active_chats:
        partner = active_chats[user_id]

        cleanup(user_id)
        cleanup(partner)

        try:
            await context.bot.send_message(
                partner,
                "❌ Stranger skipped you.",
                reply_markup=get_idle_keyboard()
            )
        except:
            pass

    await find_stranger(update, context)

# ---------------- STOP ----------------
async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in active_chats:
        partner = active_chats[user_id]

        cleanup(user_id)
        cleanup(partner)

        try:
            await context.bot.send_message(
                partner,
                "❌ Stranger ended the chat.",
                reply_markup=get_idle_keyboard()
            )
        except:
            pass

        await update.message.reply_text(
            "🛑 Chat ended.",
            reply_markup=get_idle_keyboard()
        )

    else:
        if user_id in waiting_users:
            waiting_users.remove(user_id)

        await update.message.reply_text(
            "❗ You are not in a chat.",
            reply_markup=get_idle_keyboard()
        )

# ---------------- RELAY ----------------
async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in active_chats:
        await update.message.reply_text(
            "❗ Click 'Find Stranger' first.",
            reply_markup=get_idle_keyboard()
        )
        return

    partner = active_chats[user_id]

    try:
        await update.message.copy(chat_id=partner)
    except:
        cleanup(user_id)
        cleanup(partner)

# ---------------- CLEANUP ----------------
def cleanup(user_id):
    if user_id in active_chats:
        partner = active_chats[user_id]
        active_chats.pop(user_id, None)
        active_chats.pop(partner, None)

    if user_id in waiting_users:
        waiting_users.remove(user_id)

# ---------------- MAIN ----------------
import asyncio

async def main():
    if not TOKEN:
        print("❌ BOT_TOKEN not found! Set it in environment variables.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🔍 Find Stranger$"), find_stranger))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^⏭ Next$"), next_chat))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🛑 Stop$"), stop_chat))

    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, relay))

    print("🤖 Bot is running...")

    # ✅ FIX for Python 3.14
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # keep bot alive forever
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
