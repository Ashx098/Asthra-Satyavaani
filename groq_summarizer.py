import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def summarize_title_and_text(title: str, text: str) -> str:
    """
    Summarize the following content in 4-6 bullet points, clearly formatted, using plain language and bold key names/locations if needed..
    Args:
        title (str): The title of the content.
        text (str): The main text to summarize.
    Returns:
        str: The summary returned by the GROQ API, or an error message.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"Summarize the following content.\nTitle: {title}\nText: {text}"
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes text."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256,
        "temperature": 0.5
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        today = datetime.now().strftime("%d %b %Y")
        summary = result["choices"][0]["message"]["content"].strip()
        if len(summary) > 3900:
            summary = summary[:3900] + "\n\n(Trimmed for Telegram)"
        return f"{summary}\n\n📅 Date: {today}\n🔁 Powered by Asthra Bot"
    except Exception as e:
        return f"⚠️ Summarization failed. Reason: {str(e)}"
    
