import os
import requests
import datetime
import threading
import time
from flask import Flask, request

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

app = Flask(__name__)

# ============================
# Telegram Send Function
# ============================

def send(msg):
    requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        params={"chat_id": CHAT_ID, "text": msg}
    )

# ============================
# Public Commands
# ============================

@app.route("/ping", methods=["GET"])
def ping():
    responses = [
        # Friendly diplomat
        "Alive and well — unlike your alliance next season. ⚔️",
        "Standing by, ready to negotiate… or betray.",
        "Your loyal diplomatic attaché reporting for duty. 🤝",

        # Suspiciously helpful
        "I assure you, my intentions are peaceful.",
        "Trust me. No really. Trust me. 👀",
        "I’m absolutely not supporting an attack on you right now.",

        # Classic Diplomacy humor
        "Still here — unlike Italy after 1903. 🇮🇹💀",
        "Operational. Austria should be worried.",
        "Alive, unlike Russia in most games. ❄️",

        # Scheming tone
        "I’m listening… and plotting.",
        "The bot is active. The stab is inevitable. 🗡️",
        "Alive and quietly moving pieces behind the scenes.",

        # Overly formal
        "The Ministry of Foreign Affairs acknowledges your inquiry.",
        "Your message has been received and filed under “suspicious.”",
        "Diplomatic channels are open and monitored.",

        # Deadpan
        "Yes, I’m alive. Can’t say the same for your fleets.",
        "Online. Watching. Judging your orders.",
        "Present. Unlike your army in Burgundy.",

        # Encouraging
        "Alive! You’ve got this — unless you don’t.",
        "Standing by to help you survive… barely.",
        "I believe in you. Someone has to.",
    ]
    import random
    return {"response": random.choice(responses)}

@app.route("/help", methods=["GET"])
def help():
    return {
        "commands": {
            "/ping": "Check if the bot is alive.",
            "/status": "Show next adjudication time.",
            "/gm": "Send a GM-flavored message.",
        }
    }

# ============================
# GM Message Endpoint
# ============================

@app.route("/gm", methods=["POST"])
def gm():
    data = request.json
    msg = data.get("message", "").strip()
    if not msg:
        return {"error": "Message empty"}, 400

    send(f"GM Update: {msg}")
    return {"status": "sent"}

# ============================
# Manual Send Endpoint (Front-end)
# ============================

@app.route("/send", methods=["POST"])
def send_message():
    data = request.json
    msg = data.get("message", "").strip()
    if not msg:
        return {"error": "Message empty"}, 400

    send(msg)
    return {"status": "sent"}

# ============================
# Adjudication Schedule
# ============================

# Defaults (you can override via front-end)
ADJUDICATION_TIME = "12:00"
REMINDER_TIME = "11:00"
START_DATE = "2026-08-06"

@app.route("/schedule", methods=["POST"])
def update_schedule():
    global ADJUDICATION_TIME, REMINDER_TIME, START_DATE

    data = request.json
    ADJUDICATION_TIME = data.get("adjudication_time", ADJUDICATION_TIME)
    REMINDER_TIME = data.get("reminder_time", REMINDER_TIME)
    START_DATE = data.get("start_date", START_DATE)

    return {
        "status": "updated",
        "adjudication_time": ADJUDICATION_TIME,
        "reminder_time": REMINDER_TIME,
        "start_date": START_DATE
    }

@app.route("/status", methods=["GET"])
def status():
    return {
        "adjudication_time": ADJUDICATION_TIME,
        "reminder_time": REMINDER_TIME,
        "start_date": START_DATE
    }

# ============================
# Daily Scheduler Thread
# ============================

def scheduler_loop():
    while True:
        now = datetime.datetime.now()

        # Format times
        now_str = now.strftime("%H:%M")
        today_str = now.strftime("%Y-%m-%d")

        # Reminder
        if now_str == REMINDER_TIME:
            send("⏳ Reminder: Adjudication in 1 hour!")

        # Adjudication
        if now_str == ADJUDICATION_TIME:
            send("🕒 Adjudication time has arrived!")

        time.sleep(30)  # check twice per minute

# Start scheduler thread
threading.Thread(target=scheduler_loop, daemon=True).start()

# ============================
# Run Flask
# ============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
