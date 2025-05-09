import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os
from http_request_example import fetch_mint, summarize_and_print
import time
from collections import deque

SLEEP_BETWEEN_GROQ = 15   # seconds between GROQ requests
SCRAPE_INTERVAL = 900     # every 15 minutes

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
summary_queue = deque()
processed_links = set()
seen_links = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am your Telegram bot.')

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = "https://www.livemint.com/"
    print("\n🔍 Fetching latest links...")
    latest_links = set(fetch_mint(url, reqType="top8") or [])

    new_links = latest_links - processed_links
    if new_links:
        print(f"✅ {len(new_links)} new links found.")
        for link in new_links:
            if link not in seen_links:
                seen_links[link] = time.time()
                summary_queue.append(link)
    else:
        print("No new links found.")

    # Process the queue (rate-limited)
    while summary_queue:
        link = summary_queue.popleft()
        if link not in processed_links:
            title, summary = summarize_and_print(link)
            summary = summary.replace('_', '\\_')
            full_message = f"📰 *{title}*\n\n{summary}"
            await update.message.reply_text(full_message, parse_mode="Markdown")
            time.sleep(SLEEP_BETWEEN_GROQ)

    print("🕒 Waiting for 15 minutes before next fetch...\n")
    time.sleep(SCRAPE_INTERVAL)


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('latest', latest))
    application.run_polling()

if __name__ == '__main__':
    main()