import os
import httpx
from fastapi import FastAPI, Request

app = FastAPI(title="Raj Video Zone")

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").replace("\n", "").replace("\r", "").strip()

TELEGRAM = f"https://api.telegram.org/bot{BOT_TOKEN}"
DB = f"{SUPABASE_URL}/rest/v1/videos"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


async def tg(method, data):
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{TELEGRAM}/{method}", json=data)
        return r.json()


async def db_get(params):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(DB, headers=HEADERS, params=params)
        r.raise_for_status()
        return r.json()


async def db_post(data):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            DB,
            headers={**HEADERS, "Prefer": "return=representation"},
            json=data
        )
        r.raise_for_status()
        return r.json()


@app.get("/")
def home():
    return {"project": "Raj Video Zone", "status": "Running"}


@app.get("/health")
def health():
    return {
        "status": "OK",
        "bot_configured": bool(BOT_TOKEN),
        "database_configured": bool(SUPABASE_URL and SUPABASE_KEY)
    }


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    update = await request.json()

    # নতুন ভিডিও চ্যানেল থেকে Database-এ সেভ
    post = update.get("channel_post")

    if post:
        chat = post.get("chat", {})
        video = post.get("video") or post.get("document")

        if video:
            caption = post.get("caption", "")
            title = caption[:100] if caption else "নতুন ভিডিও"

            try:
                await db_post({
                    "file_id": video["file_id"],
                    "channel_id": chat["id"],
                    "message_id": post["message_id"],
                    "title": title,
                    "caption": caption,
                    "file_size_bytes": video.get("file_size", 0)
                })
            except Exception as e:
                print("Database save error:", str(e))

        return {"ok": True}

    # ব্যবহারকারীর মেসেজ
    message = update.get("message")

    if message:
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text.startswith("/start"):
            await tg("sendMessage", {
                "chat_id": chat_id,
                "text": "❤️ স্বাগতম Raj Video Zone-এ!\n\nআপনার পছন্দের ভিডিও দেখতে নিচের বাটনে চাপ দিন।",
                "reply_markup": {
                    "inline_keyboard": [[
                        {"text": "🎬 সব ভিডিও দেখুন", "callback_data": "videos"}
                    ]]
                }
            })

        return {"ok": True}

    # বাটন চাপলে
    query = update.get("callback_query")

    if query:
        data = query.get("data")
        chat_id = query["message"]["chat"]["id"]

        await tg("answerCallbackQuery", {
            "callback_query_id": query["id"]
        })

        if data == "videos":
            try:
                videos = await db_get({
                    "select": "id,title,caption",
                    "order": "created_at.desc",
                    "limit": "10"
                })

                if not videos:
                    await tg("sendMessage", {
                        "chat_id": chat_id,
                        "text": "এখনো কোনো ভিডিও পাওয়া যায়নি।"
                    })
                else:
                    buttons = []
                    for v in videos:
                        buttons.append([{
                            "text": "🎬 " + (v["title"] or "ভিডিও"),
                            "callback_data": f"video:{v['id']}"
                        }])

                    await tg("sendMessage", {
                        "chat_id": chat_id,
                        "text": "📽️ আপনার পছন্দের ভিডিও নির্বাচন করুন:",
                        "reply_markup": {"inline_keyboard": buttons}
                    })

            except Exception as e:
                print("Video list error:", str(e))
                await tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": "দুঃখিত, ভিডিও তালিকা লোড হয়নি।"
                })

        elif data.startswith("video:"):
            video_id = data.split(":")[1]

            try:
                videos = await db_get({
                    "select": "file_id,title,caption",
                    "id": f"eq.{video_id}",
                    "limit": "1"
                })

                if videos:
                    v = videos[0]
                    await tg("sendVideo", {
                        "chat_id": chat_id,
                        "video": v["file_id"],
                        "caption": v["title"],
                        "protect_content": True
                    })
                else:
                    await tg("sendMessage", {
                        "chat_id": chat_id,
                        "text": "ভিডিওটি পাওয়া যায়নি।"
                    })

            except Exception as e:
                print("Video send error:", str(e))
                await tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": "ভিডিও চালাতে সমস্যা হয়েছে।"
                })

    return {"ok": True}


@app.get("/set-webhook")
async def set_webhook():
    return await tg("setWebhook", {
        "url": "https://raj-video-zone.onrender.com/telegram-webhook",
        "allowed_updates": [
            "message",
            "channel_post",
            "callback_query"
        ]
    })
