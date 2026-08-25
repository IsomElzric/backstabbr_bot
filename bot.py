import os
import random
import datetime
import threading
import time
import pytz
import requests
from flask import Flask, request
from email_reader import get_latest_backstabbr_email
from email_parser import parse_backstabbr_email

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GAME_URL = os.environ.get("GAME_URL")

# ============================
# Telegram Send Function
# ============================

def send(msg):
    requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        params={"chat_id": CHAT_ID, "text": msg}
    )

# ============================
# Ping Responses
# ============================

PING_RESPONSES = [
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

# ============================
# Hard-coded schedule
# ============================

CST = pytz.timezone("America/Chicago")

# First adjudication date (example: today)
FIRST_ADJUDICATION = CST.localize(datetime.datetime(2026, 8, 5, 12, 0))

# Daily adjudication time (12 PM CST)
ADJUDICATION_HOUR = 12
REMINDER_HOUR = 11
WINTER_HOUR = 12

# ============================
# Webhook Commands
# ============================

@app.route("/ping", methods=["GET"])
def ping():
    now = datetime.datetime.now(CST)

    email_body = get_latest_backstabbr_email()
    if not email_body:
        return {"error": "No Backstabbr emails found"}

    state = parse_backstabbr_email(email_body)

    # Fallback if email didn't include next adjudication
    next_adj = state["next_adj"] or next_adjudication(now)

    # Build Telegram message
    msg = (
        f"🗡️ {random.choice(PING_RESPONSES)}\n\n"
        f"📅 {state['season']} {state['year']} — {state['phase']}\n"
        f"⏱️ Next adjudication: {next_adj.strftime('%Y-%m-%d %H:%M %Z')}\n\n"
    )

    if state["retreats"]:
        msg += "🚨 Retreats required:\n"
        for p in state["retreats"]:
            msg += f"• {p}\n"
        msg += "\n"

    if state["builds"]:
        msg += "🏗️ Builds:\n"
        for p, n in state["builds"].items():
            msg += f"• {p}: {n} units\n"
        msg += "\n"

    send(msg)

    return {
        "season": state["season"],
        "year": state["year"],
        "phase": state["phase"],
        "next_adjudication": next_adj.strftime("%Y-%m-%d %H:%M %Z"),
        "retreats": state["retreats"],
        "builds": state["builds"],
        "game_url": GAME_URL
    }

# ============================
# Adjudication Logic
# ============================

def next_adjudication(now):
    """Return today's adjudication if upcoming, otherwise tomorrow."""
    today_adj = now.replace(hour=ADJUDICATION_HOUR, minute=0, second=0, microsecond=0)
    if now < today_adj:
        return today_adj
    return today_adj + datetime.timedelta(days=1)

# ============================
# Scheduler Thread
# ============================

last_reminder_date = None
last_adj_date = None

def scheduler_loop():
    global last_reminder_date, last_adj_date

    while True:
        utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        now = utc_now.astimezone(CST)
        today = now.date()

        # Reminder at 11:00 AM CST
        if now.hour == REMINDER_HOUR and now.minute == 0:
            if last_reminder_date != today:
                send("⏳ Reminder: Adjudication in 1 hour!")
                last_reminder_date = today

        # Adjudication at 12:00 PM CST
        if now.hour == ADJUDICATION_HOUR and now.minute == 0:
            if last_adj_date != today:
                tomorrow = now + datetime.timedelta(days=1)
                send(
                    f"🕒 Adjudication has completed!\n"
                    f"Next adjudication: {tomorrow.strftime('%Y-%m-%d 12:00 CST')}\n"
                    f"Game: {GAME_URL}"
                )
                last_adj_date = today

        time.sleep(30)

# Start background scheduler
threading.Thread(target=scheduler_loop, daemon=True).start()

# ============================
# Run Flask
# ============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
