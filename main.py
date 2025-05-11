import logging
import os
import re
import time
import asyncio
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
from http_request_example import fetch_mint, summarize_and_print
from keep_alive import keep_alive
from collections import deque

import requests

keep_alive()
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ASTHRA_CHANNEL_ID = os.getenv('ASTHRA_CHANNEL_ID') 

# Constants
SLEEP_BETWEEN_GROQ = 30  # Delay between summaries (3 mins)
FETCH_INTERVAL = 60      # Interval to fetch new articles (3 mins)
NO_UPDATE_NOTIFY_GAP = 900  # 30 minutes

# Globals
summary_queue = deque()
processed_links = {}
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
        logging.error(f"[IMAGE ERROR] Could not fetch image from {link}: {e}")

    return None

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("Exception while handling an update:", exc_info=context.error)

async def post_to_channel(bot, message: str, image_url: str = None):
    try:
        message = escape_markdown(message)
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
# async def news_broadcast_loop(app):
#     global last_sent_time

#     while True:
#         logging.info("🔍 Checking for latest news...")
#         print("🔍 Checking for latest news...")
#         current_time = time.time()
#         latest_links = set(fetch_mint(HOME_URL, reqType="top8") or [])
#         for link in list(processed_links):
#             if current_time - processed_links[link] > 108000:  # 6 hrs
#                 del processed_links[link]

#         new_links = latest_links - set(processed_links.keys())
#         logging.info(f"🧠 New links detected: {len(new_links)}")

#         if not new_links:
#             if current_time - last_sent_time > NO_UPDATE_NOTIFY_GAP:
#                 await post_to_channel(app.bot, "🔕 No breaking news in the last 30 minutes. Stay tuned.")
#                 last_sent_time = current_time
#             await asyncio.sleep(FETCH_INTERVAL)
#             continue

#         for link in new_links:
#             seen_links[link] = current_time
#             title, summary = await summarize_and_print(link)
#             if not title or not summary:
#                 logging.warning(f"⚠️ Skipping empty or failed summary for: {link}")
#                 continue
#             image_url = get_news_image(link)

#             full_message = f"🛡️ *Asthra Alert*\n\n*📰 {escape_markdown(title)}*\n\n{escape_markdown(summary)}"
#             chunks = [full_message[i:i + 3900] for i in range(0, len(full_message), 3900)]

#             for chunk in chunks:
#                 await post_to_channel(app.bot, chunk, image_url if chunk == chunks[0] else None)  # Only send image for first chunk (g)
#                 logging.info(f"✅ Posted chunk for: {title[:60]}...")

#             processed_links[link] = current_time
#             last_sent_time = current_time
#             await asyncio.sleep(SLEEP_BETWEEN_GROQ)

#         await asyncio.sleep(FETCH_INTERVAL)

async def background_news_job(context: ContextTypes.DEFAULT_TYPE):
    global last_sent_time
    bot = context.bot

    logging.info("\n\n\n\n**************************************************************\n🔍 Checking for latest news...\n**************************************************************\n")
    latest_links = set(fetch_mint(HOME_URL, reqType="top8") or [])
    

    # Expire old processed links
    current_time = time.time()
    logging.info(f"Last sent time: {last_sent_time}")
    logging.info(f"Current time: {current_time}")
    logging.info(f"last_sent_time - curret_time: {last_sent_time - current_time}")
    logging.info(f"NO_UPDATE_NOTIFY_GAP: {NO_UPDATE_NOTIFY_GAP}")
    for link in list(processed_links):
        if current_time - processed_links[link] > 108000:
            logging.info(f"🗑️ Expiring link: {link}")
            del processed_links[link]
    
    new_links = latest_links - set(processed_links.keys())

    if not new_links:
        if current_time - last_sent_time >= NO_UPDATE_NOTIFY_GAP:
            await post_to_channel(bot, "🔕 No breaking news in the last 30 minutes. Stay tuned.")
            last_sent_time = current_time
        return
    logging.info(f"🧠 New links found: {len(new_links)}\n***************************************************************************************\n\n")


    for link in new_links:
        title, summary = await summarize_and_print(link)

        if not title or not summary:
            logging.warning(f"⚠️ Skipping link with empty summary: {link}")
            continue
        image_url = get_news_image(link)
        full_message = f"🛡️ *Asthra Alert*\n\n*📰 {escape_markdown(title)}*\n\n{escape_markdown(summary)}"
        chunks = [full_message[i:i + 3900] for i in range(0, len(full_message), 3900)]

        for chunk in chunks:
            await post_to_channel(bot, chunk, image_url=image_url if chunk == chunks[0] else None)
            logging.info(f"##################################################################\n✅ Posted: {title[:50]}\n#############################################################################")

        processed_links[link] = time.time()
        last_sent_time = time.time()
        await asyncio.sleep(SLEEP_BETWEEN_GROQ)


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_error_handler(error_handler)

    # Schedule background job
    application.job_queue.run_repeating(
        background_news_job,
        interval=FETCH_INTERVAL,
        first=10,
        data={"last_check": time.time()}
    )

    application.run_polling()

if __name__ == '__main__':
    main()
