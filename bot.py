import os
import httpx
from fastapi import FastAPI

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

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    data = response.json()

    if data.get("ok"):
        return {
            "status": "Connected",
            "bot_username": data["result"]["username"]
        }

    return {"status": "Connection failed"}
