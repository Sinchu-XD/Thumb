import os
import re
import random
import aiohttp
import aiofiles
import numpy as np
from dotenv import load_dotenv
from pyrogram import Client, filters
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from YouTubeMusic.Search import Search

# ───────── LOAD ENV ─────────
load_dotenv()

# ───────── BOT CONFIG ─────────
API_ID = 35362137
API_HASH = "c3c3e167ea09bc85369ca2fa3c1be790"
BOT_TOKEN = "8360461005:AAH7uHgra-bYu1I3WOSgpn1VMrFt1Wi1fcw"

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError("❌ API_ID / API_HASH / BOT_TOKEN missing in .env")

# ───────── PATHS ─────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.getenv("CACHE_DIR", os.path.join(BASE_DIR, "cache"))
FONT_PATH = os.getenv("FONT_PATH", os.path.join(BASE_DIR, "fonts/Montserrat-Bold.ttf"))
FONT2_PATH = os.getenv("FONT2_PATH", os.path.join(BASE_DIR, "fonts/Roboto-Regular.ttf"))

YOUTUBE_IMG_URL = os.getenv(
    "YOUTUBE_IMG_URL",
    "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
)

os.makedirs(CACHE_DIR, exist_ok=True)

# ───────── BOT ─────────
bot = Client(
    "thumb_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ───────── HELPERS ─────────
def extract_video_id(url: str):
    try:
        if "watch?v=" in url:
            return url.split("watch?v=")[1].split("&")[0]
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
    except:
        pass
    return None


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size[0], size[1]), radius=radius, fill=255
    )
    return mask


def noise_texture(w, h, opacity=18):
    noise = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    img = Image.fromarray(noise, "RGB").convert("RGBA")
    img.putalpha(opacity)
    return img


# ───────── THUMBNAIL GENERATOR ─────────
async def gen_thumb(query: str):
    try:
        res = await Search(query, limit=1)
        if not res or not res.get("main_results"):
            return YOUTUBE_IMG_URL

        r = res["main_results"][0]

        title = r.get("title", "Unknown Title")
        duration = r.get("duration", "00:00")
        views = r.get("views", "0")
        url = r.get("url")

        vid = extract_video_id(url)
        if not vid:
            return YOUTUBE_IMG_URL

        thumb_url = r.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        final_path = os.path.join(CACHE_DIR, f"{vid}.png")

        if os.path.isfile(final_path):
            return final_path

        raw_path = os.path.join(CACHE_DIR, f"raw_{vid}.jpg")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status != 200:
                    return YOUTUBE_IMG_URL
                async with aiofiles.open(raw_path, "wb") as f:
                    await f.write(await resp.read())

        img = Image.open(raw_path).convert("RGBA")

        # ─── CANVAS ───
        W, H = 1920, 1080
        canvas = Image.new("RGBA", (W, H))

        bg = img.resize((W, H), Image.LANCZOS)
        bg = ImageEnhance.Color(bg).enhance(1.3)
        bg = bg.filter(ImageFilter.GaussianBlur(70))
        bg = ImageEnhance.Brightness(bg).enhance(0.55)
        canvas.paste(bg, (0, 0))

        canvas.paste(noise_texture(W, H), (0, 0), noise_texture(W, H))

        # ─── CARD ───
        card_w, card_h = 1100, 380
        cx, cy = (W - card_w) // 2, (H - card_h) // 2

        card = Image.new("RGBA", (card_w, card_h))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle(
            (0, 0, card_w, card_h),
            radius=40,
            fill=(15, 15, 20, 160),
            outline=(255, 255, 255, 40),
            width=2
        )

        try:
            f_title = ImageFont.truetype(FONT_PATH, 46)
            f_meta = ImageFont.truetype(FONT2_PATH, 28)
            f_small = ImageFont.truetype(FONT2_PATH, 24)
        except:
            f_title = f_meta = f_small = ImageFont.load_default()

        album = img.resize((300, 300), Image.LANCZOS)
        card.paste(album, (40, 40), rounded_mask((300, 300), 28))

        clean = re.sub(r"[^\w\s\-\.\,\!\?]", "", title)
        if len(clean) > 30:
            clean = clean[:27] + "..."

        cd.text((380, 55), clean, font=f_title, fill="white")
        cd.text((380, 115), f"👁 {views}", font=f_meta, fill=(220, 220, 220))
        cd.text((380, 165), f"⏱ {duration}", font=f_small, fill=(190, 190, 190))

        canvas.paste(card, (cx, cy), card)
        canvas.convert("RGB").save(final_path, "PNG")

        os.remove(raw_path)
        return final_path

    except Exception as e:
        print("[THUMB ERROR]", e)
        return YOUTUBE_IMG_URL


# ───────── BOT COMMAND ─────────
@bot.on_message(filters.command("thumb"))
async def thumb_cmd(_, m):
    if len(m.command) < 2:
        return await m.reply("❌ Usage:\n`/thumb song name`")

    msg = await m.reply("🎨 Generating thumbnail...")
    thumb = await gen_thumb(" ".join(m.command[1:]))

    if thumb.startswith("http"):
        await msg.edit("❌ Failed to generate thumbnail")
    else:
        await m.reply_photo(thumb)
        await msg.delete()


# ───────── START ─────────
bot.run()
    
