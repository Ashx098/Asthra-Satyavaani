import logging
import os
import re
import time
import asyncio
import requests
from bs4 import BeautifulSoup
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

def get_news_image(link):
    """
    Extracts a representative image from the news article page.
    Prioritizes og:image, then twitter:image, then first <img>, then returns None.
    """
    try:
        response = requests.get(link, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']

        # Try Twitter card image
        twitter_image = soup.find('meta', property='twitter:image')
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']

        # Fallback to first visible <img> on page
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and src.startswith("http"):
                return src

    except Exception as e:
        print(f"[IMAGE ERROR] Could not fetch image from {link}: {e}")

    return None

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Exception while handling an update:", exc_info=context.error)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Hello! I am Asthra Satyavaani.\n""I post verified, AI-summarized breaking news in our Telegram Channel:\n" "📢 Join here: https://t.me/asthrasatyavaani")

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("✅ Real-time Updates are being automatically posted to our channel.\nJoin: https://t.me/asthrasatyavaani")

async def post_to_channel(bot, message: str, image_url: str = None):
    try:
        if image_url:
            await bot.send_photo(
                chat_id=ASTHRA_CHANNEL_ID,
                photo=image_url,
                caption=message[:1024],  # Telegram caption limit
                parse_mode="MarkdownV2"
            )
        else:
            await bot.send_message(
                chat_id=ASTHRA_CHANNEL_ID,
                text=message,
                parse_mode="MarkdownV2"
            )
    except Exception as e:
        print(f"❌ Error posting to Telegram: {e}")

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
