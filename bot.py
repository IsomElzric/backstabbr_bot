import requests
from bs4 import BeautifulSoup
import time
import json
import re
import os

GAME_URL = os.environ.get("GAME_URL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_FILE = "state.json"

# Load state (phase + whether we already warned)
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_phase": None, "warned_phase": None}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send(msg):
    requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        params={"chat_id": CHAT_ID, "text": msg}
    )

def get_phase_and_deadline():
    html = requests.get(GAME_URL).text
    soup = BeautifulSoup(html, "html.parser")

    phase = soup.select_one(".phase-title").get_text(strip=True)
    deadline = soup.select_one(".deadline-timer").get_text(strip=True)

    return phase, deadline

state = load_state()

while True:
    try:
        phase, deadline = get_phase_and_deadline()

        # Detect new season
        if state["last_phase"] and phase != state["last_phase"]:
            send(f"🆕 New season started: {phase}")
            state["warned_phase"] = None  # reset warning for new phase

        state["last_phase"] = phase

        # Detect adjudication approaching (1 hour threshold)
        if state["warned_phase"] != phase:
            match = re.search(r"(\d+)", deadline)
            if match:
                minutes = int(match.group(1))
                if "hour" in deadline:
                    minutes *= 60

                if minutes <= 60:
                    send(f"⏳ Adjudication in about an hour! Current phase: {phase}")
                    state["warned_phase"] = phase

        save_state(state)

    except Exception as e:
        print("Error:", e)

    time.sleep(60)
