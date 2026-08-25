import os
import imaplib
import email

EMAIL = os.environ.get("EMAIL_ADDRESS")
PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"

def get_latest_backstabbr_email():
    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        # Search for Backstabbr emails
        result, data = mail.search(None, '(FROM "backstabbr.com")')
        if result != "OK":
            return None

        ids = data[0].split()
        if not ids:
            return None

        latest_id = ids[-1]

        # Fetch the latest email
        result, msg_data = mail.fetch(latest_id, "(RFC822)")
        if result != "OK":
            return None

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Extract plain text body
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode("utf-8")

        # Fallback to snippet-like content
        return msg.get("subject", "")

    except Exception as e:
        return f"IMAP error: {e}"
