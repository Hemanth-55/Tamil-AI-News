"""Deliver a message to WhatsApp. Configure ONE of these with GitHub Actions secrets (both are free):

  Green-API (free Developer plan; links a WhatsApp account like WhatsApp Web)
    GREEN_API_URL     e.g. https://7103.api.greenapi.com   (shown on your instance page)
    GREEN_ID          idInstance
    GREEN_TOKEN       apiTokenInstance
    WHATSAPP_CHAT_ID  where to send: your number as 1XXXXXXXXXX@c.us, or a group id ending in @g.us

  CallMeBot (free for personal use, when it has open slots)
    CALLMEBOT_PHONE   your number with country code, e.g. +1XXXXXXXXXX
    CALLMEBOT_KEY     the API key the bot sends you

With nothing configured, the briefing is only written to digests/ (preview mode).
"""
import os, time
import requests

LIMIT = 3800  # stay under WhatsApp's message length limit


def chunks(text):
    out, cur = [], ""
    for para in text.split("\n\n"):
        if len(cur) + len(para) + 2 > LIMIT and cur:
            out.append(cur); cur = ""
        cur = (cur + "\n\n" + para) if cur else para
    return out + [cur] if cur else out


def whatsapp(text):
    env = os.environ.get
    if env("GREEN_ID") and env("GREEN_TOKEN") and env("WHATSAPP_CHAT_ID"):
        base = (env("GREEN_API_URL") or "https://api.green-api.com").rstrip("/")
        url = f"{base}/waInstance{env('GREEN_ID')}/sendMessage/{env('GREEN_TOKEN')}"
        for part in chunks(text):
            r = requests.post(url, json={"chatId": env("WHATSAPP_CHAT_ID"), "message": part}, timeout=30)
            print("green-api", r.status_code)
            if r.status_code >= 300:
                return False
            time.sleep(2)
        return True
    if env("CALLMEBOT_PHONE") and env("CALLMEBOT_KEY"):
        for part in chunks(text):
            r = requests.get("https://api.callmebot.com/whatsapp.php",
                             params={"phone": env("CALLMEBOT_PHONE"), "text": part, "apikey": env("CALLMEBOT_KEY")}, timeout=30)
            print("callmebot", r.status_code)
            if r.status_code >= 300:
                return False
            time.sleep(3)
        return True
    print("preview mode: no WhatsApp secrets set; briefing saved to digests/")
    return True
