from pyrogram import Client
import os
import asyncio
from thumbnails import get_thumb

API_ID = 35362137
API_HASH = "c3c3e167ea09bc85369ca2fa3c1be790"
BOT_TOKEN = "8360461005:AAH7uHgra-bYu1I3WOSgpn1VMrFt1Wi1fcw"

app = Client("testbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message()
async def send_thumb(client, message):
    thumb = await get_thumb(
        title="Test Song",
        duration="2:45",
        thumbnail="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        channel="Test Channel",
        views="1M",
        videoid="abc123"
    )
    await message.reply_photo(thumb)

app.run()
