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

import requests

keep_alive()
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ASTHRA_CHANNEL_ID = os.getenv('ASTHRA_CHANNEL_ID') 

# Constants
SLEEP_BETWEEN_GROQ = 300  # Delay between summaries (3 mins)
FETCH_INTERVAL = 300      # Interval to fetch new articles (3 mins)
NO_UPDATE_NOTIFY_GAP = 1800  # 30 minutes

# Globals
summary_queue = deque()
processed_links = {}
seen_links = {}
last_sent_time = time.time()
HOME_URL = "https://www.livemint.com/"

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
    await update.message.reply_text("👋 Hello! I am Asthra Satyavaani.\n""I post verified, AI-summarized breaking news in our Telegram Channel:\n" "📢 Join here: https://t.me/asthrasatyavaani")

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("✅ Real-time Updates are being automatically posted to our channel.\nJoin: https://t.me/asthrasatyavaani")

async def post_to_channel(bot, message: str):
    try:
        await bot.send_message(chat_id=ASTHRA_CHANNEL_ID, text=message, parse_mode="MarkdownV2")
    except Exception as e:
        logging.error(f"Failed to post to channel: {e}")

# Background fetch + post loop
async def news_broadcast_loop(app):
    global last_sent_time

    while True:
        logging.info("🔍 Checking for latest news...")
        print("🔍 Checking for latest news...")
        current_time = time.time()
        latest_links = set(fetch_mint(HOME_URL, reqType="top8") or [])
        for link in list(processed_links):
            if current_time - processed_links[link] > 108000:  # 6 hrs
                del processed_links[link]

        new_links = latest_links - set(processed_links.keys())
        logging.info(f"🧠 New links detected: {len(new_links)}")

        if not new_links:
            if current_time - last_sent_time > NO_UPDATE_NOTIFY_GAP:
                await post_to_channel(app.bot, "🔕 No breaking news in the last 30 minutes. Stay tuned.")
                last_sent_time = current_time
            await asyncio.sleep(FETCH_INTERVAL)
            continue

        for link in new_links:
            seen_links[link] = current_time
            title, summary = await summarize_and_print(link)

            if not title or not summary:
                logging.warning(f"⚠️ Skipping empty or failed summary for: {link}")
                continue

            full_message = f"🛡️ *Asthra Alert*\n\n*📰 {escape_markdown(title)}*\n\n{escape_markdown(summary)}"
            chunks = [full_message[i:i + 3900] for i in range(0, len(full_message), 3900)]

            for chunk in chunks:
                await post_to_channel(app.bot, chunk)
                logging.info(f"✅ Posted chunk for: {title[:60]}...")

            processed_links[link] = current_time
            last_sent_time = current_time
            await asyncio.sleep(SLEEP_BETWEEN_GROQ)

        await asyncio.sleep(FETCH_INTERVAL)

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_error_handler(error_handler)

    # Bot commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('latest', latest))

        # Start loop after app launch
    async def on_startup(app):
        app.create_task(news_broadcast_loop(app))

    application.post_init = on_startup

    # Start bot
    application.run_polling()

if __name__ == '__main__':
    main()