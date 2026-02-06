import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pyrogram import Client, filters
from YouTubeMusic.Search import Search

# ───────── CONFIG ─────────
API_ID = 35362137
API_HASH = "c3c3e167ea09bc85369ca2fa3c1be790"
BOT_TOKEN = "8360461005:AAH7uHgra-bYu1I3WOSgpn1VMrFt1Wi1fcw"

FONT_SONG = "fonts/Montserrat-Bold.ttf"
FONT_META = "fonts/Roboto-Medium.ttf"
FONT_STATS = "fonts/JetBrainsMono-Regular.ttf"

os.makedirs("temp", exist_ok=True)

bot = Client(
    "pil_thumb_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ───────── HELPERS ─────────
def extract_video_id(url: str):
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None


def yt_thumbnail(url: str):
    vid = extract_video_id(url)
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"


async def get_thumb_from_query(query: str):
    res = await Search(query, limit=1)
    if not res or not res.get("main_results"):
        return None

    i = res["main_results"][0]
    return {
        "title": i.get("title", "Unknown"),
        "duration": i.get("duration", "Unknown"),
        "views": i.get("views", "Unknown"),
        "thumb": i.get("thumbnail") or yt_thumbnail(i["url"]),
    }

# ───────── PIL THUMBNAIL ─────────
def generate_thumbnail(data: dict) -> str:
    # download image
    r = requests.get(data["thumb"])
    img = Image.open(BytesIO(r.content)).convert("RGB")

    # canvas
    canvas = Image.new("RGB", (900, 900))
    bg = img.resize((900, 900)).filter(ImageFilter.GaussianBlur(18))
    canvas.paste(bg, (0, 0))

    # circular album
    album = img.resize((260, 260))
    mask = Image.new("L", album.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, 260, 260), fill=255)

    canvas.paste(album, (80, 320), mask)

    # text
    draw = ImageDraw.Draw(canvas)

    font_title = ImageFont.truetype(FONT_SONG, 46)
    font_meta = ImageFont.truetype(FONT_META, 28)
    font_views = ImageFont.truetype(FONT_STATS, 26)

    draw.text((380, 330), data["title"], font=font_title, fill="white")
    draw.text((380, 395), data["duration"], font=font_meta, fill="#cccccc")
    draw.text((380, 435), data["views"], font=font_views, fill="#aaaaaa")

    out = "temp/final.jpg"
    canvas.save(out, "JPEG", quality=92)
    return out

# ───────── BOT CMD ─────────
@bot.on_message(filters.command("thumb"))
async def thumb(_, m):
    if len(m.command) < 2:
        return await m.reply("Usage: /thumb song name")

    msg = await m.reply("🎧 Designing thumbnail...")
    data = await get_thumb_from_query(" ".join(m.command[1:]))

    if not data:
        return await msg.edit("❌ Not found")

    file = generate_thumbnail(data)
    await m.reply_photo(file)
    await msg.delete()

bot.run()
