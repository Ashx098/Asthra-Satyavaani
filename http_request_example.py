import aiohttp
import asyncio
import logging
import json
from bs4 import BeautifulSoup
from groq_summarizer import summarize_title_and_text

logging.basicConfig(level=logging.INFO)

async def fetch_html(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            logging.info(f"🌐 [FETCH] URL: {url} Status: {response.status}")
            return await response.text()
    except Exception as e:
        logging.error(f"❌ Error fetching {url}: {e}")
        return None

async def fetch_mint(url, reqType):
    async with aiohttp.ClientSession() as session:
        html = await fetch_html(session, url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        if reqType == "top8":
            breaking_news_urls = []
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "ItemList":
                        for item in data.get("itemListElement", []):
                            link = item.get("url")
                            if link and link.startswith("https://www.livemint.com/"):
                                breaking_news_urls.append(link)
                except Exception as e:
                    logging.warning(f"⚠️ Skipping malformed JSON block: {e}")
            return breaking_news_urls

        elif reqType == "news":
            try:
                title = soup.title.string.strip() if soup.title else "Untitled"
                article_body = ""
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and data.get("@type") == "NewsArticle":
                            article_body = data.get("articleBody", "")
                            break
                    except Exception as e:
                        logging.warning(f"⚠️ Error in JSON parsing in news: {e}")
                return title, article_body
            except Exception as e:
                logging.error(f"❌ Error parsing article: {e}")
                return None

async def summarize_and_print(link):
    logging.info(f"🔗 Summarizing: {link}")
    try:
        result = await fetch_mint(link, reqType="news")
        if result:
            title, body = result
            if title and body:
                summary = summarize_title_and_text(title, body)
                logging.info(f"✅ Summarized: {title[:50]}...")
                return title, summary
            else:
                logging.warning("⚠️ Missing title/body content")
                return None, None
        return None, None
    except Exception as e:
        logging.error(f"❌ Summarization failed for {link}: {e}")
        return None, None
