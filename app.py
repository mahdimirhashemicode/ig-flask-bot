# app.py
import os
import logging
from flask import Flask, request
import requests

app = Flask(__name__)

# ===========================
# Logging Setup
# ===========================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DEBUG_WEBHOOK = os.getenv("DEBUG_WEBHOOK", "false").lower() == "true"

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ===========================
# Environment Variables
# ===========================
VERIFY_TOKEN = os.getenv("IG_VERIFY_TOKEN", "CHANGE_ME_VERIFY_TOKEN")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "CHANGE_ME_ACCESS_TOKEN")
IG_BUSINESS_ID = os.getenv("IG_BUSINESS_ID", "CHANGE_ME_IG_BUSINESS_ID")
GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


# ===========================
# Routes
# ===========================
@app.route("/", methods=["GET"])
def home():
    return "Instagram Flask Webhook is running ✅ v2", 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # --------------------------
    # 1) Verification (GET)
    # --------------------------
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        app.logger.info(f"[VERIFY] mode={mode}, token={token}")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Verification token mismatch", 403

    # --------------------------
    # 2) Event Handling (POST)
    # --------------------------
    if DEBUG_WEBHOOK:
        raw_body = request.data.decode("utf-8", errors="ignore")
        headers = dict(request.headers)
        app.logger.debug("=== IG WEBHOOK POST RECEIVED ===")
        app.logger.debug(f"Headers: {headers}")
        app.logger.debug(f"Raw body: {raw_body}")

    data = request.get_json(silent=True)
    app.logger.info(f"[WEBHOOK] Incoming POST (object={data.get('object') if data else 'None'})")

    if not data or "entry" not in data:
        app.logger.warning("[WEBHOOK] No entry in payload.")
        return "EVENT_RECEIVED", 200

    for entry in data["entry"]:
        for change in entry.get("changes", []):
            field = change.get("field")
            value = change.get("value", {})

            app.logger.info(f"[WEBHOOK] Change received: {field}")

            if field == "comments":
                handle_comment_event(value)

    return "EVENT_RECEIVED", 200


# ===========================
# Comment Event Handler
# ===========================
def handle_comment_event(value: dict):
    comment_text = value.get("text", "")
    user = value.get("from", {})
    user_id = user.get("id")
    username = user.get("username")

    media = value.get("media", {})
    media_id = media.get("id")
    media_type = media.get("media_product_type")

    # Pretty compact one-line log for comments
    app.logger.info(
        f"[COMMENT] user={username}({user_id}), media={media_id}/{media_type}, text={comment_text!r}"
    )

    if not user_id:
        app.logger.warning("[COMMENT] Missing user_id → cannot send DM.")
        return

    txt = comment_text.strip()
    if txt == "1":
        send_dm(user_id, "🎤 سرنخ ۱: خواننده‌ی این آهنگ یه آقای معروفه تو سبک پاپ!")
    elif txt == "2":
        send_dm(user_id, "🎶 سرنخ ۲: ژانر آهنگ پاپ شادِ مخصوص رقص!")
    elif txt == "3":
        send_dm(user_id, "😉 سرنخ ۳: اسم آهنگ با حرف 'د' شروع میشه!")
    else:
        app.logger.info(f"[COMMENT] No action for text={txt!r}")


# ===========================
# DM Sender
# ===========================
def send_dm(user_ig_id: str, message: str):
    app.logger.info(f"[DM] → Sending DM to {user_ig_id}: {message}")

    if IG_ACCESS_TOKEN.startswith("CHANGE_ME"):
        app.logger.warning("[DM] IG_ACCESS_TOKEN not set — skipping real send.")
        return

    # (Enable real send when you activate messaging)
    # endpoint = f"{GRAPH_API_BASE}/{IG_BUSINESS_ID}/messages"
    # payload = {
    #     "recipient": {"id": user_ig_id},
    #     "message": {"text": message}
    # }
    # params = {"access_token": IG_ACCESS_TOKEN}
    # res = requests.post(endpoint, json=payload, params=params)
    # app.logger.info(f"[DM] Response {res.status_code}: {res.text}")

    # Mock for now
    app.logger.info(f"[DM] Mock send OK → user={user_ig_id}")


# ===========================
# Run local
# ===========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
