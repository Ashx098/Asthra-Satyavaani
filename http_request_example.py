import requests
from bs4 import BeautifulSoup
import json
import time
from collections import deque
from groq_summarizer import summarize_title_and_text  # Your GROQ summarizer function


def fetch_mint(url, reqType):
    try:
        response = requests.get(url)
        print(f"📥 Status Code: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")

        if reqType == "top8":
                breaking_news_urls = []
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and data.get("@type") == "ItemList":
                            for item in data.get("itemListElement", []):
                                url = item.get("url")
                                if url and url.startswith("https://www.livemint.com/"):
                                    breaking_news_urls.append(url)
                    except Exception:
                        continue
                return breaking_news_urls


        elif reqType == "news":
            page_title = soup.title.string.strip()
            article_body = ""
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "NewsArticle":
                        article_body = data.get("articleBody", "")
                        break
                except Exception:
                    continue
            return page_title, article_body
    except requests.RequestException as e:
        print(f"⚠️ Error fetching {url}: {e}")
        return None

def summarize_and_print(link):
    try:
        result = fetch_mint(link, reqType="news")
        if result:
            title, body = result
            if title and body:
                print(f"\n📌 Summarizing: {title}\n🔗 {link}")
                summary = summarize_title_and_text(title, body)
                print(summary)
                return title,summary
            else:
                print("⚠️ Missing title or body, skipping...")
                return None,None
        processed_links.add(link)
    except Exception as e:
        print(f"❌ Summarization failed for {link}: {e}")


if __name__ == "__main__":
    main_loop()
