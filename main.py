import logging
import os
import re
import time
import asyncio
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, ContextTypes, JobQueue
from telegram.constants import ParseMode
from http_request_example import fetch_mint, summarize_and_print
from keep_alive import keep_alive

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ASTHRA_CHANNEL_ID = os.getenv('ASTHRA_CHANNEL_ID')

if not BOT_TOKEN or not ASTHRA_CHANNEL_ID:
    raise ValueError("Missing BOT_TOKEN or ASTHRA_CHANNEL_ID in environment")

# Constants
SLEEP_BETWEEN_GROQ = int(os.getenv("SLEEP_BETWEEN_GROQ", 900))
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", 2000))
NO_UPDATE_NOTIFY_GAP = int(os.getenv("NO_UPDATE_NOTIFY_GAP", 4000))
HOME_URL = "https://www.livemint.com/"

# Globals
processed_links = {}
last_sent_time = time.time()

# Logger
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def escape_markdown(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def get_news_image(link):
    """Extract preview image from article."""
    try:
        response = requests.get(link, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        for prop in ['og:image', 'twitter:image']:
            meta = soup.find('meta', property=prop)
            if meta and meta.get('content'):
                return meta['content']

        for img in soup.find_all('img'):
            src = img.get('src')
            if src and src.startswith("http"):
                return src

    except Exception as e:
        logging.warning(f"[IMAGE] Failed to fetch image: {e}")
    return None

async def post_to_channel(bot, message: str, image_url: str = None):
    try:
        if image_url:
            await bot.send_photo(chat_id=ASTHRA_CHANNEL_ID, photo=image_url, caption=message[:1024], parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await bot.send_message(chat_id=ASTHRA_CHANNEL_ID, text=message, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.error(f"❌ Error posting to Telegram: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Exception while handling update:", exc_info=context.error)

async def background_news_job(context: ContextTypes.DEFAULT_TYPE):
    global last_sent_time
    bot = context.bot
    current_time = time.time()
    logging.info("\n🔍 Checking for latest news...")

    latest_links = set(await fetch_mint(HOME_URL, reqType="top8") or [])

    # Expire old links (6 hrs)
    for link in list(processed_links):
        if current_time - processed_links[link] > 21600:
            del processed_links[link]

    new_links = latest_links - set(processed_links.keys())
    logging.info(f"🧠 Found {len(new_links)} new links")

    if not new_links:
        if current_time - last_sent_time >= NO_UPDATE_NOTIFY_GAP:
            await post_to_channel(bot, escape_markdown("🔕 No breaking news in the last 1 hour. Stay tuned."))
            last_sent_time = current_time
        return

    for link in new_links:
        try:
            title, summary = await summarize_and_print(link)
            if not title or not summary:
                continue

            image_url = get_news_image(link)
            full_message = f"🛡️ *Asthra Alert*\n\n*📰 {escape_markdown(title)}*\n\n{escape_markdown(summary)}"
            chunks = [full_message[i:i+3900] for i in range(0, len(full_message), 3900)]

            for chunk in chunks:
                await post_to_channel(bot, chunk, image_url=image_url if chunk == chunks[0] else None)

            processed_links[link] = time.time()
            last_sent_time = time.time()
            await asyncio.sleep(SLEEP_BETWEEN_GROQ)

        except Exception as e:
            logging.error(f"❌ Failed to process {link}: {e}")

def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_error_handler(error_handler)

    app.job_queue.run_repeating(
        background_news_job,
        interval=FETCH_INTERVAL,
        first=10,
        job_kwargs={"max_instances": 1}
    )

    app.run_polling()

if __name__ == '__main__':
    main()
