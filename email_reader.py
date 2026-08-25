import os
import imaplib
import email

EMAIL = os.environ.get("EMAIL_ADDRESS")
PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")
IMAP_SERVER = "imap.gmail.com"

def get_latest_backstabbr_email():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        # 1️⃣ Search for UNREAD Backstabbr emails
        result, data = mail.search(None, '(FROM "backstabbr.com" UNSEEN)')
        if result != "OK":
            return None

        ids = data[0].split()

        # 2️⃣ If no unread emails, fall back to latest Backstabbr email
        if not ids:
            result, data = mail.search(None, '(FROM "backstabbr.com")')
            if result != "OK":
                return None
            ids = data[0].split()
            if not ids:
                return None

        latest_id = ids[-1]

        # 3️⃣ Fetch the email
        result, msg_data = mail.fetch(latest_id, "(RFC822)")
        if result != "OK":
            return None

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # 4️⃣ Mark email as READ
        mail.store(latest_id, '+FLAGS', '\\Seen')

        # 5️⃣ Extract plain text body
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode("utf-8")

        return msg.get("subject", "")

    except Exception as e:
        return f"IMAP error: {e}"
