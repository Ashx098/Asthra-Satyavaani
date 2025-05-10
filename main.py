import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os
import re
from http_request_example import fetch_mint, summarize_and_print
import time
from collections import deque
from keep_alive import keep_alive
keep_alive()

SLEEP_BETWEEN_GROQ = 180   # seconds between GROQ requests
SCRAPE_INTERVAL = 1500     # every 15 minutes

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

def escape_markdown(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logging.error("Exception while handling an update:", exc_info=context.error)
    # Optionally, send a message to a specific chat ID to notify about the error
    # traceback_str = ''.join(traceback.format_exception(None, context.error, context.error.__traceback__))
    # await context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=f"An error occurred: {context.error}\n{traceback_str[:4000]}")


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
            safe_title = escape_markdown(title)
            safe_summary = escape_markdown(summary)
            full_message = f"🛡️ *Asthra Alert*\n\n*📰 {safe_title}*\n\n{safe_summary}"
            chunks = [full_message[i:i+3900] for i in range(0, len(full_message), 3900)]

            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode="MarkdownV2")
            time.sleep(SLEEP_BETWEEN_GROQ)

    print("🕒 Waiting for 15 minutes before next fetch...\n")
    time.sleep(SCRAPE_INTERVAL)


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    # Add an error handler
    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('latest', latest))
    application.run_polling()

if __name__ == '__main__':
    main()