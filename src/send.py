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


def green_image(env, path, caption):
    """Send the front page as a picture. Uses the instance's media host (GREEN_MEDIA_URL, or derived from GREEN_API_URL)."""
    base = (env("GREEN_API_URL") or "https://api.green-api.com").rstrip("/")
    media = (env("GREEN_MEDIA_URL") or base.replace(".api.", ".media.").replace("//api.", "//media.")).rstrip("/")
    for host in dict.fromkeys([media, base]):
        try:
            with open(path, "rb") as f:
                r = requests.post(f"{host}/waInstance{env('GREEN_ID')}/sendFileByUpload/{env('GREEN_TOKEN')}",
                                  data={"chatId": env("WHATSAPP_CHAT_ID"), "caption": caption},
                                  files={"file": (os.path.basename(path), f, "image/png")}, timeout=60)
            print("green-api image", r.status_code)
            if r.status_code < 300:
                return True
        except Exception as ex:
            print("green-api image failed", type(ex).__name__)
    return False


def whatsapp(text, image=None, caption=""):
    env = os.environ.get
    if env("GREEN_ID") and env("GREEN_TOKEN") and env("WHATSAPP_CHAT_ID"):
        base = (env("GREEN_API_URL") or "https://api.green-api.com").rstrip("/")
        if image:
            green_image(env, image, caption)          # the text still goes out if the picture fails
            time.sleep(2)
        url = f"{base}/waInstance{env('GREEN_ID')}/sendMessage/{env('GREEN_TOKEN')}"
        for part in chunks(text):
            r = requests.post(url, json={"chatId": env("WHATSAPP_CHAT_ID"), "message": part}, timeout=30)
            print("green-api", r.status_code)
            if r.status_code >= 300:
                return False, f"green-api error {r.status_code}"
            time.sleep(2)
        return True, "green-api"
    if env("CALLMEBOT_PHONE") and env("CALLMEBOT_KEY"):
        for part in chunks(text):
            r = requests.get("https://api.callmebot.com/whatsapp.php",
                             params={"phone": env("CALLMEBOT_PHONE"), "text": part, "apikey": env("CALLMEBOT_KEY")}, timeout=30)
            print("callmebot", r.status_code)
            if r.status_code >= 300:
                return False, f"callmebot error {r.status_code}"
            time.sleep(3)
        return True, "callmebot"
    print("preview mode: no WhatsApp secrets set; briefing saved to digests/")
    return True, "preview (no WhatsApp secrets found)"
