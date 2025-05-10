import logging
import os
import re
import time
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from http_request_example import fetch_mint, summarize_and_print
from keep_alive import keep_alive
from collections import deque

keep_alive()
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ASTHRA_CHANNEL_ID = os.getenv('ASTHRA_CHANNEL_ID') 

SLEEP_BETWEEN_GROQ = 180   # seconds
HOME_URL = "https://www.livemint.com/"

summary_queue = deque()
processed_links = set()
seen_links = {}

# Logging config
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def escape_markdown(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Exception while handling an update:", exc_info=context.error)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Hello! I am Asthra Satyavaani.\nYou’ll get verified news updates in our Telegram Channel: @asthrasatyavaani.")

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("✅ Updates are being automatically posted to our channel.\nJoin: https://t.me/asthrasatyavaani")

async def post_to_channel(bot, message: str):
    await bot.send_message(chat_id=ASTHRA_CHANNEL_ID, text=message, parse_mode="MarkdownV2")

# Background fetch + post loop
async def news_broadcast_loop(app):
    while True:
        print("🔍 Checking for latest news...")
        latest_links = set(fetch_mint(HOME_URL, reqType="top8") or [])
        new_links = latest_links - processed_links

        if new_links:
            print(f"✅ Found {len(new_links)} new links.")
            for link in new_links:
                if link not in seen_links:
                    seen_links[link] = time.time()
                    try:
                        title, summary = summarize_and_print(link)
                        full_message = f"🛡️ *Asthra Alert*\n\n*📰 {escape_markdown(title)}*\n\n{escape_markdown(summary)}"
                        chunks = [full_message[i:i+3900] for i in range(0, len(full_message), 3900)]
                        for chunk in chunks:
                            await post_to_channel(app.bot, chunk)
                        processed_links.add(link)
                        time.sleep(SLEEP_BETWEEN_GROQ)
                    except Exception as e:
                        print(f"❌ Error summarizing/sending link: {e}")
        else:
            print("No new links found.")
        await asyncio.sleep(180)  # wait 3 minutes

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_error_handler(error_handler)

    # Bot commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('latest', latest))

    async def on_startup(app):
        app.create_task(news_broadcast_loop(app))

    application.post_init = on_startup

    # Start bot
    application.run_polling()

if __name__ == '__main__':
    main()