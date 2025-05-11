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
    await update.message.reply_text("👋 Hello! I am Asthra Satyavaani.\nYou’ll get verified news updates in our Telegram Channel: @asthrasatyavaani.")

async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("✅ Updates are being automatically posted to our channel.\nJoin: https://t.me/asthrasatyavaani")

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
                        image_url = get_news_image(link)

                        full_message = f"🛡️ *Asthra Alert*\n\n*📰 {escape_markdown(title)}*\n\n{escape_markdown(summary)}"
                        chunks = [full_message[i:i+3900] for i in range(0, len(full_message), 3900)]

                        for chunk in chunks:
                            await post_to_channel(app.bot, chunk, image_url if chunk == chunks[0] else None)

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
