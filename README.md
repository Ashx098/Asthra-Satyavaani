# 🌟 Asthra Satyavaani — Real-time Verified News Summarizer Bot

> 🇮🇳 Serving the Nation with Truth, Not Hype.

Satyavaani is a powerful Telegram bot built under the **Asthra AI initiative** that delivers **real-time, verified, and AI-summarized national news** directly to users. Whether during times of national conflict, policy change, or public concern, Satyavaani ensures the public receives fast, reliable, and factual news from sources like **Livemint**, PIB, MoD, and other trusted platforms.

---

## 🔍 Demo

Join the official bot here: [@asthraabot](https://t.me/asthraabot)

![Screenshot](screenshot.png) <!-- Replace with your actual screenshot path -->

---

## 🧭 How to Use (Telegram)

📱 Open @asthraabot in Telegram

🟢 Press Start to activate the bot

🔘 Use the /latest command to fetch the most recent verified news

📰 The bot will scrape top headlines, summarize them using LLaMA 3 (via GROQ), and send clean, bullet-point summaries

🔁 Come back anytime or wait for future scheduled updates

You can also add this bot to your group or channel to keep everyone informed with fact-checked, AI-driven news.

---

## 📄 Features

* 🌐 **Scrapes LiveMint.com** for top national headlines
* 🤖 **Uses GROQ's LLaMA 3 API** to generate clean, bullet-point summaries
* ♻️ Maintains a **smart queue system** to avoid duplicate summaries and API rate limits
* ⌛ Refreshes **every 15 minutes** for new content
* 📢 Pushes formatted news into Telegram with date, verification stamp, and bot signature
* 📊 Trims or splits messages to respect Telegram's 4096 char limit
* ✅ Markdown-safe formatting for enhanced readability

---

## 🧬 Use Cases

* Conflict-zone info relay (e.g., India vs Pakistan tensions)
* Misinformation countering during high-alert events
* Real-time civic journalism
* Daily brief delivery for teachers, journalists, or NGOs
* National security alert networks

---

## 🛠️ Tech Stack

* **Python 3.10+**
* `python-telegram-bot`
* `httpx`, `requests`, `beautifulsoup4`
* **GROQ API** (LLaMA3/8B model)
* `dotenv` for API token security
* `deque`, `set`, and pointer logic for queue management

---

## 📁 Folder Structure

```
.
├── main.py                      # Telegram bot setup & command handlers
├── http_request_example.py     # Scraping logic + queue
├── groq_summarizer.py          # GROQ API summarization handler
├── .env                        # API tokens (BOT_TOKEN, GROQ_API_KEY)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
```

---

## ✨ Sample Message Output

```
🛡️ Asthra Alert

📰 FM Sitharaman urges banks to prepare for crisis amid India-Pakistan tensions

• Directed banks to ensure uninterrupted financial services
• Cyber audits & upgraded protocols required
• Emphasized nationwide resilience in finance sector

🗓️ 10 May 2025
🔁 Powered by Asthra Bot
```

---

## 🌟 Roadmap

* [x] Telegram delivery with summarization
* [x] Smart queue and rate-limiting
* [ ] DDNews/PIB multi-source support
* [ ] Hindi/Regional language summaries
* [ ] Admin panel for manual broadcast
* [ ] Auto-publish to a public Telegram Channel

---

## 💼 License

MIT License

---

## 📑 Credits

Built with love by [Avinash Mynampati](https://aviinashh-ai.vercel.app/) and [Roshan Ali](github.com/RoshanAli339) under the **Asthra AI** initiative.

This project represents the belief that **factual news and clarity** are the strongest defense against fear, fake news, and conflict.

> "Let the truth speak. Let Satyavaani rise."

---

Let me know if you want to auto-deploy this to Heroku, Dockerize, or generate badges/logos!
