import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from YouTubeMusic.Search import Search

# ───────── CONFIG ─────────
API_ID = 35362137
API_HASH = "c3c3e167ea09bc85369ca2fa3c1be790"
BOT_TOKEN = "8360461005:AAH7uHgra-bYu1I3WOSgpn1VMrFt1Wi1fcw"

FONT_SONG = "fonts/Montserrat-Bold.ttf"
FONT_DURATION = "fonts/Roboto-Medium.ttf"
FONT_VIEWS = "fonts/JetBrainsMono.ttf"

os.makedirs("temp", exist_ok=True)

bot = Client(
    "music_thumb_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ───────── YT HELPERS ─────────
def extract_video_id(url: str):
    try:
        if "watch?v=" in url:
            return url.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
    except Exception:
        pass
    return None


def yt_thumbnail(url: str):
    vid = extract_video_id(url)
    if not vid:
        return None
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"


# ───────── QUERY → DATA ─────────
async def get_thumb_from_query(query: str):
    res = await Search(query, limit=1)
    if not res or not res.get("main_results"):
        return None

    i = res["main_results"][0]
    vid = extract_video_id(i["url"])
    if not vid:
        return None

    return {
        "title": i.get("title", "Unknown Title"),
        "duration": i.get("duration", "Unknown"),
        "views": i.get("views", "Unknown"),
        "thumb": i.get("thumbnail") or yt_thumbnail(i["url"]),
    }


# ───────── FFMPEG THUMB GENERATOR ─────────
def generate_thumbnail(data: dict) -> str:
    thumb_url = data["thumb"]
    title = data["title"].replace("'", "")
    duration = data["duration"]
    views = data["views"]

    bg = "temp/bg.jpg"
    circle = "temp/circle.png"
    final = "temp/final.jpg"

    # 1️⃣ Background
    subprocess.run([
        "ffmpeg", "-y", "-i", thumb_url,
        "-vf", "scale=900:900,boxblur=35:1,eq=brightness=-0.08:saturation=1.1",
        bg
    ], check=True)

    # 2️⃣ Circular thumbnail
    subprocess.run([
        "ffmpeg", "-y", "-i", thumb_url,
        "-vf",
        "scale=300:300,format=rgba,"
        "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
        "a='if(lte((X-150)^2+(Y-150)^2,150^2),255,0)'",
        circle
    ], check=True)

    # 3️⃣ Final composition
    subprocess.run([
        "ffmpeg", "-y",
        "-i", bg,
        "-i", circle,
        "-filter_complex",
        f"""
        overlay=(W-w)/2:(H-h)/2,
        drawtext=fontfile={FONT_SONG}:
        text='{title}':
        fontsize=52:
        fontcolor=white:
        x=360:y=560,
        drawtext=fontfile={FONT_DURATION}:
        text='{duration}':
        fontsize=30:
        fontcolor=#cccccc:
        x=360:y=625,
        drawtext=fontfile={FONT_VIEWS}:
        text='{views}':
        fontsize=28:
        fontcolor=#aaaaaa:
        x=360:y=665
        """,
        final
    ], check=True)

    return final


# ───────── BOT COMMAND ─────────
@bot.on_message(filters.command("thumb") & filters.private)
async def thumb_cmd(_, m: Message):
    if len(m.command) < 2:
        return await m.reply("❌ Usage:\n`/thumb song name`")

    query = " ".join(m.command[1:])
    msg = await m.reply("🎧 Generating thumbnail...")

    try:
        data = await get_thumb_from_query(query)
        if not data:
            return await msg.edit("❌ Song not found")

        file = generate_thumbnail(data)
        await m.reply_photo(file)
        await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ Error:\n`{e}`")


bot.run()
  
