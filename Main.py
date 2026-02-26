import asyncio
from pyrogram import Client, filters
from YouTubeMusic.Search import Search
from thumbnails import get_thumb

API_ID = 35362137
API_HASH = "c3c3e167ea09bc85369ca2fa3c1be790"
BOT_TOKEN = "8231818663:AAFtLagnRx0OSfIBO_a0RcXWkgRIExJsOqQ"

app = Client("ThumbBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start"))
async def play_handler(client, message):

    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: /play song name")

    query = " ".join(message.command[1:])
    await message.reply_text("🔎 Searching...")

    results = await Search(query, limit=1)

    if not results or not results.get("main_results"):
        return await message.reply_text("❌ No Results Found")

    item = results["main_results"][0]

    # 🔥 Extract Properly
    title = item.get("title", "Unknown Title")
    duration = item.get("duration", "Live")

    # Thumbnail handling (list or string)
    thumbnail = item.get("thumbnail")
    if isinstance(thumbnail, list):
        thumbnail = thumbnail[0]["url"]

    channel = item.get("channel", "Unknown Channel")
    views = item.get("views", "1M")
    videoid = item.get("id", "testid")

    # 🎨 Generate Thumbnail
    thumb_path = await get_thumb(
        title=title,
        duration=duration,
        thumbnail=thumbnail,
        channel=channel,
        views=views,
        videoid=videoid
    )

    if not thumb_path:
        return await message.reply_text("❌ Thumbnail Generate Failed")

    caption = f"""
🎵 **{title}**

⏱ Duration : {duration}
📺 Channel : {channel}
👀 Views : {views}
"""

    await message.reply_photo(photo=thumb_path, caption=caption)


app.run()
