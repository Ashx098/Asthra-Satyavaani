from flask import Flask
from threading import Thread
import logging
import socket

app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Asthra Bot is Alive"

def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run():
    port = 8080
    if is_port_in_use(port):
        logging.info(f"🔄 Port {port} is already in use, Flask server likely already running")
        return
    
    logging.info("🟢 Flask keep_alive server started...")
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e):
            logging.info("🔄 Flask server already running on another thread")
        else:
            logging.error(f"❌ Flask server error: {e}")

def keep_alive():
    # Check if server is already running
    if is_port_in_use(8080):
        logging.info("🔄 Keep-alive server already running")
        return
        
    t = Thread(target=run, daemon=True)  # Mark as daemon to prevent blocking
    t.start()
