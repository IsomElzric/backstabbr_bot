import os
import time
import json
import re
import random
import threading

import requests
from bs4 import BeautifulSoup
from flask import Flask, request

GAME_URL = os.environ.get("GAME_URL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_FILE = "state.json"

app = Flask(__name__)


# ---------- State helpers ----------

def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "last_phase": None,
            "warned_phase": None,
            "last_season_from": None,
            "last_season_to": None,
        }
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


state = load_state()


# ---------- Telegram helpers ----------

def send(msg, chat_id=CHAT_ID):
    if not TELEGRAM_TOKEN or not chat_id:
        print("Missing TELEGRAM_TOKEN or CHAT_ID")
        return

    requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        params={"chat_id": chat_id, "text": msg}
    )


# ---------- Backstabbr scraping ----------

def get_phase_and_deadline():
    session_cookie = os.environ.get("BACKSTABBR_SESSION")
    game_url = os.environ.get("GAME_URL")

    if not game_url:
        print("ERROR: GAME_URL is not set")
        return "Unknown phase", "Unknown deadline"

    html = requests.get(
        game_url,
        cookies={"session": session_cookie} if session_cookie else None
    ).text

    soup = BeautifulSoup(html, "html.parser")

    phase_el = soup.select_one(".phase-title")
    deadline_el = soup.select_one(".deadline-timer")

    phase = phase_el.get_text(strip=True) if phase_el else "Unknown phase"
    deadline = deadline_el.get_text(strip=True) if deadline_el else "Unknown deadline"

    return phase, deadline


def parse_deadline_to_minutes(deadline_text):
    # Examples:
    # "1 hour 23 minutes"
    # "23 minutes"
    # "2 hours"
    text = deadline_text.lower()

    hours = 0
    minutes = 0

    h_match = re.search(r"(\d+)\s*hour", text)
    m_match = re.search(r"(\d+)\s*minute", text)

    if h_match:
        hours = int(h_match.group(1))
    if m_match:
        minutes = int(m_match.group(1))

    total = hours * 60 + minutes
    return total if total > 0 else None


def extract_season_label(phase_text):
    # e.g. "Spring 1903 – Orders" -> "Spring 1903"
    return phase_text.split("–")[0].strip() if "–" in phase_text else phase_text.strip()


# ---------- /ping personality ----------

PING_LINES = [
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


# ---------- Telegram webhook ----------

@app.route("/", methods=["POST"])
def webhook():
    data = request.json or {}

    message = data.get("message")
    if not message:
        return "OK", 200

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.startswith("/ping"):
        line = random.choice(PING_LINES)
        send(line, chat_id)

    elif text.startswith("/phase"):
        phase, _ = get_phase_and_deadline()
        send(f"Current phase: {phase}", chat_id)

    elif text.startswith("/deadline"):
        _, deadline = get_phase_and_deadline()
        send(f"Deadline: {deadline}", chat_id)

    elif text.startswith("/status"):
        phase, deadline = get_phase_and_deadline()
        minutes = parse_deadline_to_minutes(deadline)

        orders_due = "Yes" if "orders" in phase.lower() else "No"

        if state.get("last_season_from") and state.get("last_season_to"):
            last_change = f"{state['last_season_from']} → {state['last_season_to']}"
        else:
            last_change = "Unknown"

        lines = [
            f"Phase: {phase}",
            f"Deadline: {deadline}",
            f"Time until adjudication: {minutes} minutes" if minutes is not None else "Time until adjudication: Unknown",
            f"Orders due: {orders_due}",
            f"Last season change: {last_change}",
        ]

        send("\n".join(lines), chat_id)

    return "OK", 200


# ---------- Background Backstabbr loop ----------

def background_loop():
    global state

    while True:
        try:
            phase, deadline = get_phase_and_deadline()
            current_season = extract_season_label(phase)

            # Detect season change
            if state["last_phase"]:
                prev_season = extract_season_label(state["last_phase"])
                if current_season != prev_season:
                    send(f"🆕 New season started: {current_season}")
                    state["last_season_from"] = prev_season
                    state["last_season_to"] = current_season
                    state["warned_phase"] = None

            state["last_phase"] = phase

            # Adjudication warning (about an hour)
            if state["warned_phase"] != phase:
                minutes = parse_deadline_to_minutes(deadline)
                if minutes is not None and minutes <= 60:
                    send(f"⏳ Adjudication in about an hour! Current phase: {phase}")
                    state["warned_phase"] = phase

            save_state(state)

        except Exception as e:
            print("Error in loop:", e)

        time.sleep(60)


# ---------- Start everything ----------

def start_background():
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()


start_background()

if __name__ == "__main__":
    # Render will expect a port; use PORT env or default 10000
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
