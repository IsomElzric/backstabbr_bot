import requests
import json

# ============================
# CONFIGURE THIS
# ============================

GM_ENDPOINT = "https://backstabbr-bot.onrender.com/gm"

# Optional: If you want a secret key later, we can add it here.
SECRET = None

# ============================
# MAIN LOOP
# ============================

def send_gm_message(msg):
    payload = {"message": msg}

    if SECRET:
        payload["secret"] = SECRET

    try:
        res = requests.post(GM_ENDPOINT, json=payload)
        if res.status_code == 200:
            print("✔ GM message sent successfully!")
        else:
            print(f"✖ Server responded with {res.status_code}: {res.text}")
    except Exception as e:
        print("✖ Error sending message:", e)


def main():
    print("Diplomacy GM Broadcaster")
    print("-------------------------")
    print("Type your message and press Enter.")
    print("Type 'exit' to quit.\n")

    while True:
        msg = input("GM> ").strip()
        if msg.lower() == "exit":
            print("Goodbye.")
            break
        if not msg:
            continue

        send_gm_message(msg)


if __name__ == "__main__":
    main()
