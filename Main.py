import asyncio
from YouTubeMusic.Search import Search
from thumbnails import get_thumb

async def main():
    print("🔎 Searching Song...")

    results = await Search("Kesariya", limit=1)

    if not results or not results.get("main_results"):
        print("❌ No Results Found")
        return

    item = results["main_results"][0]

    # 🔥 Extract Data Safely
    title = item.get("title", "Unknown Title")
    duration = item.get("duration", "Live")
    thumbnail = item.get("thumbnail")
    channel = item.get("channel", "Unknown Channel")
    views = item.get("views", "1M")
    videoid = item.get("id", "testid")

    print("🎵 Title:", title)
    print("⏱ Duration:", duration)
    print("📺 Channel:", channel)

    print("🖼 Generating Thumbnail...")

    thumb_path = await get_thumb(
        title=title,
        duration=duration,
        thumbnail=thumbnail,
        channel=channel,
        views=views,
        videoid=videoid
    )

    if thumb_path:
        print("✅ Thumbnail Generated Successfully!")
        print("📂 Saved At:", thumb_path)
    else:
        print("❌ Failed To Generate Thumbnail")

if __name__ == "__main__":
    asyncio.run(main())
