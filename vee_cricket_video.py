import os
import re
import html
import urllib.request
import subprocess
from datetime import datetime, timezone, timedelta
from io import BytesIO

import feedparser
from PIL import Image, ImageDraw, ImageFont

IST = timezone(timedelta(hours=5, minutes=30))
OUT = "vee_cricket_faceless.mp4"
WORK = "vee_cricket_video_work"
W, H = 1080, 1920
FPS = 30

FEEDS = {
    "Team India": "https://news.google.com/rss/search?q=Team+India+cricket+OR+BCCI&hl=en-IN&gl=IN&ceid=IN:en",
    "Cricket Trending": "https://news.google.com/rss/search?q=cricket+India+trending&hl=en-IN&gl=IN&ceid=IN:en",
    "IPL": "https://news.google.com/rss/search?q=IPL+cricket&hl=en-IN&gl=IN&ceid=IN:en",
}

FONT = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
FONT_B = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
ENG_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def clean(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(text or "")))
    return re.sub(r"\s+", " ", text).strip()


def image_url(entry):
    for key in ("media_content", "media_thumbnail"):
        for m in entry.get(key, []) or []:
            if isinstance(m, dict) and m.get("url"):
                return m["url"]
    return ""


def get_items():
    items = []
    for category, url in FEEDS.items():
        feed = feedparser.parse(url)
        for e in feed.entries[:10]:
            title = clean(e.get("title", ""))
            link = e.get("link", "")
            if not title or not link:
                continue
            source = ""
            try:
                source = clean(e.source.get("title", ""))
            except Exception:
                pass
            if not source:
                source = title.rsplit(" - ", 1)[-1]
            summary = clean(e.get("summary", "") or e.get("description", ""))
            items.append({
                "title": re.sub(r"\s+-\s+[^-]+$", "", title).strip(),
                "summary": summary[:500],
                "link": link,
                "source": source,
                "image": image_url(e),
                "published": e.get("published_parsed"),
                "category": category,
            })
    return items


def choose(items):
    # Google News RSS is already ordered by recent relevance.
    # Prefer a recent Indian cricket item with a usable headline.
    return items[0] if items else None


def download_image(url):
    if not url:
        return None
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read(8 * 1024 * 1024)
        return Image.open(BytesIO(data)).convert("RGB")
    except Exception as exc:
        print("Image download skipped:", exc)
        return None


def cover(img):
    if img is None:
        img = Image.new("RGB", (W, H), (8, 24, 65))
        d = ImageDraw.Draw(img)
        d.text((80, 700), "CRICKET", font=ImageFont.truetype(ENG_B, 100), fill=(255, 210, 0))
        d.text((80, 830), "NEWS", font=ImageFont.truetype(ENG_B, 100), fill="white")
        return img
    ratio = max(W / img.width, H / img.height)
    nw, nh = int(img.width * ratio), int(img.height * ratio)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - W) // 2, (nh - H) // 2
    return img.crop((left, top, left + W, top + H))


def wrap(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = word if not cur else cur + " " + word
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def make_frames(item):
    os.makedirs(WORK, exist_ok=True)
    bg = cover(download_image(item["image"]))
    title = item["title"][:180]
    summary = item["summary"] or "क्रिकेट से जुड़ी यह ताजा खबर चर्चा में है।"

    f_title = ImageFont.truetype(FONT_B, 58)
    f_body = ImageFont.truetype(FONT_B, 38)
    f_small = ImageFont.truetype(FONT_B, 28)
    f_eng = ImageFont.truetype(ENG_B, 34)

    # Three scenes, 20 seconds each. Same source photo is used with different crops.
    for i in range(3):
        frame = bg.copy()
        d = ImageDraw.Draw(frame, "RGBA")

        # Dark overlays improve readability while keeping the news photo visible.
        d.rectangle([0, 0, W, 210], fill=(5, 20, 55, 225))
        d.rectangle([0, 1500, W, H], fill=(5, 20, 55, 235))
        d.rectangle([0, 0, 18, H], fill=(221, 24, 31, 255))

        d.rounded_rectangle([42, 38, 280, 118], 18, fill=(221, 24, 31, 255))
        d.text((73, 55), "VEE NEWS", font=f_eng, fill="white")
        d.text((330, 48), "क्रिकेट अपडेट", font=f_title, fill=(255, 210, 0))

        if i == 0:
            lines = wrap(d, title, f_title, 920)[:4]
            y = 1540
            for line in lines:
                d.text((55, y), line, font=f_title, fill="white")
                y += 72
        elif i == 1:
            d.text((55, 1515), "मुख्य अपडेट", font=f_title, fill=(255, 210, 0))
            lines = wrap(d, summary, f_body, 930)[:6]
            y = 1600
            for line in lines:
                d.text((55, y), line, font=f_body, fill="white")
                y += 53
        else:
            d.text((55, 1530), "स्रोत", font=f_title, fill=(255, 210, 0))
            d.text((55, 1610), item["source"][:45], font=f_body, fill="white")
            d.text((55, 1700), "ताजा क्रिकेट खबरों के लिए", font=f_body, fill="white")
            d.text((55, 1760), "Vee News को फॉलो करें", font=f_body, fill=(255, 210, 0))
            d.text((55, 1840), datetime.now(IST).strftime("%d %b %Y | %H:%M IST"), font=f_small, fill="white")

        frame.save(os.path.join(WORK, f"frame{i}.jpg"), quality=92)


def make_voice(item):
    script = (
        "नमस्कार। Vee News पर क्रिकेट की ताजा खबर। "
        + item["title"] + ". "
        + (item["summary"][:300] if item["summary"] else "इस खबर से जुड़ी ताजा जानकारी सामने आई है।")
        + " अधिक अपडेट के लिए Vee News को फॉलो करें।"
    )
    with open(os.path.join(WORK, "script.txt"), "w", encoding="utf-8") as f:
        f.write(script)
    subprocess.run(
        ["espeak-ng", "-v", "hi", "-s", "145", "-p", "45", "-w", os.path.join(WORK, "voice.wav"), script],
        check=True,
    )


def make_video():
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", os.path.join(WORK, "frame0.jpg"),
        "-loop", "1", "-i", os.path.join(WORK, "frame1.jpg"),
        "-loop", "1", "-i", os.path.join(WORK, "frame2.jpg"),
        "-i", os.path.join(WORK, "voice.wav"),
        "-filter_complex",
        "[0:v]scale=1080:1920,setsar=1[v0];"
        "[1:v]scale=1080:1920,setsar=1[v1];"
        "[2:v]scale=1080:1920,setsar=1[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[v]",
        "-map", "[v]", "-map", "3:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
        "-c:a", "aac", "-b:a", "96k",
        "-pix_fmt", "yuv420p", "-shortest", "-movflags", "+faststart",
        OUT
    ], check=True)


def main():
    items = get_items()
    item = choose(items)
    if not item:
        raise RuntimeError("No cricket news found.")
    print("Selected topic:", item["title"])
    print("Source:", item["source"])
    make_frames(item)
    make_voice(item)
    make_video()
    print("VIDEO_CREATED:", OUT)


if __name__ == "__main__":
    main()
