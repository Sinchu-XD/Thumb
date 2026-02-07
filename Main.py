import os
import re
import inspect
import aiohttp
import aiofiles
import numpy as np
from dotenv import load_dotenv
from pyrogram import Client, filters
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from YouTubeMusic.Search import Search

# ───────── LOAD ENV ─────────
load_dotenv()

API_ID = int(os.getenv("API_ID", "35362137"))
API_HASH = os.getenv("API_HASH", "c3c3e167ea09bc85369ca2fa3c1be790")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8360461005:AAH7uHgra-bYu1I3WOSgpn1VMrFt1Wi1fcw")

# ───────── PATHS ─────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
FONT_PATH = os.path.join(BASE_DIR, "fonts/Montserrat-Bold.ttf")
FONT2_PATH = os.path.join(BASE_DIR, "fonts/Roboto-Regular.ttf")

YOUTUBE_IMG_URL = "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
os.makedirs(CACHE_DIR, exist_ok=True)

# ───────── BOT ─────────
bot = Client(
    "thumb_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ───────── HELPERS ─────────
def extract_video_id(url):
    if not url:
        return None
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *size), radius, fill=255)
    return mask


def noise_texture(w, h, opacity=18):
    noise = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    img = Image.fromarray(noise, "RGB").convert("RGBA")
    img.putalpha(opacity)
    return img


def draw_text_shadow(draw, pos, text, font, fill):
    x, y = pos
    draw.text((x+2, y+2), text, font=font, fill=(0, 0, 0, 200))
    draw.text((x, y), text, font=font, fill=fill)


# ───────── THUMB GENERATOR ─────────
async def gen_thumb(query):
    try:
        result = Search(query, limit=1)
        res = await result if inspect.iscoroutine(result) else result

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

        final_path = os.path.join(CACHE_DIR, f"{vid}.png")
        if os.path.isfile(final_path):
            return final_path

        thumb_url = r.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        raw_path = os.path.join(CACHE_DIR, f"raw_{vid}.jpg")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                async with aiofiles.open(raw_path, "wb") as f:
                    await f.write(await resp.read())

        img = Image.open(raw_path).convert("RGBA")

        # ───────── CANVAS ─────────
        W, H = 1920, 1080
        canvas = Image.new("RGBA", (W, H))

        bg = img.resize((W, H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(80))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)
        bg = ImageEnhance.Color(bg).enhance(1.4)
        canvas.paste(bg, (0, 0))

        noise = noise_texture(W, H)
        canvas.paste(noise, (0, 0), noise)

        # ───────── PLAYER CARD ─────────
        card_w, card_h = 1250, 300
        cx, cy = (W - card_w) // 2, (H - card_h) // 2

        card = Image.new("RGBA", (card_w, card_h))
        cd = ImageDraw.Draw(card)

        cd.rounded_rectangle(
            (0, 0, card_w, card_h),
            radius=40,
            fill=(10, 10, 12, 220)
        )

        # Fonts
        try:
            f_title = ImageFont.truetype(FONT_PATH, 38)
            f_meta = ImageFont.truetype(FONT2_PATH, 24)
        except:
            f_title = f_meta = ImageFont.load_default()

        # Album
        album = img.resize((220, 220), Image.LANCZOS)
        card.paste(album, (30, 40), rounded_mask((220, 220), 28))

        clean = re.sub(r"[^\w\s\-.,!?]", "", title)
        if len(clean) > 40:
            clean = clean[:37] + "..."

        # Text (VISIBLE FIX)
        draw_text_shadow(cd, (280, 55), clean, f_title, (255, 255, 255))
        draw_text_shadow(cd, (280, 115), f"👁 {views}", f_meta, (230, 230, 230))
        draw_text_shadow(cd, (280, 155), f"⏱ {duration}", f_meta, (210, 210, 210))

        canvas.paste(card, (cx, cy), card)
        canvas.convert("RGB").save(final_path, "PNG")

        os.remove(raw_path)
        return final_path

    except Exception as e:
        print("[THUMB ERROR]", e)
        return YOUTUBE_IMG_URL


# ───────── COMMAND ─────────
@bot.on_message(filters.command("thumb"))
async def thumb_cmd(_, m):
    if len(m.command) < 2:
        return await m.reply("❌ /thumb song name")

    msg = await m.reply("🎨 Generating thumbnail...")
    thumb = await gen_thumb(" ".join(m.command[1:]))

    if isinstance(thumb, str) and thumb.startswith("http"):
        await msg.edit("❌ Failed to generate thumbnail")
    else:
        await m.reply_photo(thumb)
        await msg.delete()


# ───────── START ─────────
bot.run()
