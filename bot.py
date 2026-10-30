import os
import httpx
from fastapi import FastAPI, Request

app = FastAPI(title="Raj Video Zone")

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://raj-video-zone.onrender.com/telegram-webhook"

latest_video_data = None


async def telegram_call(method, payload):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
            json=payload
        )
        return response.json()


@app.get("/")
def home():
    return {
        "project": "Raj Video Zone",
        "status": "Backend Running"
    }


@app.get("/health")
def health():
    return {
        "status": "OK",
        "bot_configured": bool(BOT_TOKEN)
    }


@app.get("/telegram-check")
async def telegram_check():
    if not BOT_TOKEN:
        return {"status": "BOT_TOKEN missing"}

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        )

    return response.json()


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    global latest_video_data

    update = await request.json()

    message = update.get("message") or update.get("channel_post")

    if not message:
        return {"ok": True}

    chat = message.get("chat", {})

    if message.get("text", "").startswith("/start"):
        await telegram_call(
            "sendMessage",
            {
                "chat_id": chat["id"],
                "text": "স্বাগতম! ❤️ Raj Video Zone চালু আছে।"
            }
        )

    video = message.get("video") or message.get("document")

    if video:
        file_size = video.get("file_size", 0)

        latest_video_data = {
            "status": "Video Found",
            "channel_id": chat.get("id"),
            "message_id": message.get("message_id"),
            "file_id": video.get("file_id"),
            "caption": message.get("caption", ""),
            "file_size_bytes": file_size,
            "file_size_MB": round(file_size / 1048576, 2)
        }

    return {"ok": True}


@app.get("/set-webhook")
async def set_webhook():
    if not BOT_TOKEN:
        return {"status": "BOT_TOKEN missing"}

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={
                "url": WEBHOOK_URL,
                "allowed_updates": ["message", "channel_post"]
            }
        )

    return response.json()


@app.get("/latest-video")
async def latest_video():
    if latest_video_data:
        return latest_video_data

    return {"status": "No video found yet"}


@app.get("/video-info")
async def video_info():
    if latest_video_data:
        return {
            "status": "Video Found",
            "file_size_bytes": latest_video_data.get("file_size_bytes"),
            "file_size_MB": latest_video_data.get("file_size_MB")
        }

    return {"status": "No video found yet"}
