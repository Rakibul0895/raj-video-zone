import os
import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Raj Video Zone API")

BOT_TOKEN = os.getenv("BOT_TOKEN")

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

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        )

    data = response.json()

    if data.get("ok"):
        return {
            "status": "Connected",
            "bot_username": data["result"]["username"]
        }

    return {"status": "Connection failed"}

@app.get("/latest-video")
async def latest_video():
    if not BOT_TOKEN:
        raise HTTPException(500, "BOT_TOKEN missing")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            url,
            params={"allowed_updates": '["channel_post"]'}
        )

    data = response.json()

    if not data.get("ok"):
        return {"status": "Telegram update error"}

    for update in reversed(data.get("result", [])):
        post = update.get("channel_post", {})
        media = post.get("video") or post.get("document")

        if media:
            return {
                "status": "Video Found",
                "channel_id": post["chat"]["id"],
                "message_id": post["message_id"],
                "file_id": media["file_id"],
                "caption": post.get("caption", "")
            }

    return {"status": "No video found"}
@app.get("/video-info")
async def video_info():
    if not BOT_TOKEN:
        return {"status": "BOT_TOKEN missing"}

    async with httpx.AsyncClient(timeout=30) as client:
        updates = await client.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
            params={"allowed_updates": '["channel_post"]'}
        )

        data = updates.json()

        for update in reversed(data.get("result", [])):
            post = update.get("channel_post", {})
            video = post.get("video") or post.get("document")

            if video:
                return {
                    "status": "Video Found",
                    "file_size_bytes": video.get("file_size"),
                    "file_size_MB": round(
                        video.get("file_size", 0) / 1048576, 2
                    )
                }

    return {"status": "No video found"}
