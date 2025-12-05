# app.py
import os
import logging
import sys

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# لاگ ساده برای دیباگ روی Render
logging.basicConfig(level=logging.INFO)

# این‌ها رو بعداً توی Environment (روی Render) ست می‌کنی
VERIFY_TOKEN = os.getenv("IG_VERIFY_TOKEN", "CHANGE_ME_VERIFY_TOKEN")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "CHANGE_ME_ACCESS_TOKEN")
IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID", "CHANGE_ME_IG_BUSINESS_ID")
GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


@app.route("/", methods=["GET"])
def home():
    return "Instagram Flask Webhook is running ✅", 200


# یک روت واحد برای GET (verification) و POST (eventها)
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # ---------- 1) Webhook Verification (GET) ----------
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        app.logger.info(f"[WEBHOOK GET] mode={mode}, token={token}")
        print(f"[WEBHOOK GET] mode={mode}, token={token}")
        sys.stdout.flush()

        if mode == "subscribe" and token == VERIFY_TOKEN:
            # توکن صحیح است → hub.challenge را برگردان
            return challenge, 200
        else:
            return "Verification token mismatch", 403

    # ---------- 2) دریافت Event ها (POST) ----------
    # برای اینکه مطمئن بشیم هر POST لاگ میشه:
    raw_body = request.data.decode("utf-8", errors="ignore")
    headers = dict(request.headers)

    app.logger.info("=== IG WEBHOOK POST RECEIVED ===")
    app.logger.info(f"Headers: {headers}")
    app.logger.info(f"Raw body: {raw_body}")
    print("=== IG WEBHOOK POST RECEIVED ===")
    print("Headers:", headers)
    print("Raw body:", raw_body)
    sys.stdout.flush()

    # اگر JSON درست فرستاده شده باشه:
    data = request.get_json(silent=True)
    app.logger.info(f"Parsed JSON: {data}")

    # ساختار کلی webhook اینستاگرام
    # {
    #   "object": "instagram",
    #   "entry": [
    #     {
    #       "id": "PAGE_OR_IG_ID",
    #       "changes": [
    #         {
    #           "field": "comments",
    #           "value": { ... }
    #         }
    #       ]
    #     }
    #   ]
    # }

    if data and "entry" in data:
        for entry in data["entry"]:
            changes = entry.get("changes", [])
            for change in changes:
                field = change.get("field")
                value = change.get("value", {})

                # مثال: اگر رویداد مربوط به کامنت بود
                if field == "comments":
                    handle_comment_event(value)

                # اگر بعداً خواستی پیام‌های DM رو هم بگیری:
                # if field == "messages":
                #     handle_message_event(value)

    # همیشه 200 برگردون که IG راضی باشه
    return "EVENT_RECEIVED", 200


def handle_comment_event(value: dict):
    """
    این تابع رویداد کامنت رو می‌گیرد.
    در اینجا می‌تونی متن کامنت، اسم کاربر و... رو بخونی.
    """
    app.logger.info(f"Handling comment event: {value}")
    print(f"Handling comment event: {value}")
    sys.stdout.flush()

    # مثال ساختار value تقریبی:
    # {
    #   "id": "comment_id",
    #   "text": "1",
    #   "from": { "id": "user_ig_id" }
    # }

    comment_text = value.get("text", "")
    from_user = value.get("from", {})
    user_id = from_user.get("id")

    app.logger.info(f"Comment text: {comment_text}, from user: {user_id}")
    print(f"Comment text: {comment_text}, from user: {user_id}")
    sys.stdout.flush()

    if not user_id:
        return

    comment_text_stripped = comment_text.strip()

    if comment_text_stripped == "1":
        send_dm(user_id, "🎤 سرنخ ۱: خواننده‌ی این آهنگ یه آقای معروفه تو سبک پاپ!")
    elif comment_text_stripped == "2":
        send_dm(user_id, "🎶 سرنخ ۲: ژانر آهنگ پاپ شادِ مخصوص رقص!")
    elif comment_text_stripped == "3":
        send_dm(user_id, "😉 سرنخ ۳: اسم آهنگ با حرف 'د' شروع میشه!")
    else:
        # اگر چیز دیگه‌ای نوشت، می‌تونی جواب عمومی بدی یا هیچی ندی
        # send_dm(user_id, "برای گرفتن سرنخ، عدد 1 یا 2 یا 3 رو کامنت کن 😉")
        pass


def send_dm(user_ig_id: str, message: str):
    """
    این تابع باید با Instagram Graph API یک پیام DM برای کاربر بفرستد.
    """
    app.logger.info(f"Trying to send DM to {user_ig_id}: {message}")
    print(f"Trying to send DM to {user_ig_id}: {message}")
    sys.stdout.flush()

    if IG_ACCESS_TOKEN.startswith("CHANGE_ME"):
        app.logger.warning("IG_ACCESS_TOKEN not set properly, skipping actual DM send.")
        return

    # مثال کلی (قبل از استفاده واقعی، مستندات رسمی رو چک کن):
    # endpoint = f"{GRAPH_API_BASE}/{IG_BUSINESS_ID}/messages"
    # payload = {
    #     "recipient": {"id": user_ig_id},
    #     "message": {"text": message}
    # }
    # params = {
    #     "access_token": IG_ACCESS_TOKEN
    # }
    # res = requests.post(endpoint, json=payload, params=params)
    # app.logger.info(f"DM send response: {res.status_code} - {res.text}")

    # فعلاً فقط ماک:
    app.logger.info(f"Mock send DM: to={user_ig_id}, message={message}")
    print(f"Mock send DM: to={user_ig_id}, message={message}")
    sys.stdout.flush()


if __name__ == "__main__":
    # برای تست لوکال
    app.run(host="0.0.0.0", port=5000)
