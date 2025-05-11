from flask import Flask
from threading import Thread
import logging

app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Asthra Bot is Alive"

def run():
    logging.info("🟢 Flask keep_alive server started...")
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run, daemon=True)  # Mark as daemon to prevent blocking
    t.start()
