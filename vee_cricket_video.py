import os
import re
import html
import json
import urllib.parse
import urllib.request
import subprocess
from datetime import datetime, timezone, timedelta
from io import BytesIO

import feedparser
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont

IST = timezone(timedelta(hours=5, minutes=30))
OUT = "vee_cricket_faceless.mp4"
WORK = "vee_cricket_video_work"
W, H = 1080, 1920
SCENE_SECONDS = 10

FEEDS = {
    "टीम इंडिया": "https://news.google.com/rss/search?q=Team+India+cricket+OR+BCCI&hl=hi-IN&gl=IN&ceid=IN:hi",
    "क्रिकेट ट्रेंडिंग": "https://news.google.com/rss/search?q=cricket+India+trending&hl=hi-IN&gl=IN&ceid=IN:hi",
    "आईपीएल": "https://news.google.com/rss/search?q=IPL+cricket&hl=hi-IN&gl=IN&ceid=IN:hi",
}

HINDI = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
ENG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ENG_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def clean(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(text or "")))
    return re.sub(r"\s+", " ", text).strip()


def is_hindi_char(ch):
    return 0x0900 <= ord(ch) <= 0x097F


def is_bad_image_url(url):
    low = str(url or "").lower()
    return any(x in low for x in (
        "google.com", "googleusercontent.com", "gstatic.com",
        "googleapis.com", "news.google.com"
    ))


def article_image_url(link):
    if not link:
        return ""
    try:
        req = urllib.request.Request(
            link,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/153 Safari/537.36"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read(900000)
        text = raw.decode("utf-8", errors="ignore")
        patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image',
        ]
        for pattern in patterns:
            m = re.search(pattern, text, flags=re.I)
            if m and not is_bad_image_url(m.group(1)):
                return html.unescape(m.group(1))
    except Exception as exc:
        print("Article image lookup skipped:", exc)
    return ""


def rss_image(entry):
    for key in ("media_content", "media_thumbnail"):
        for m in entry.get(key, []) or []:
            if isinstance(m, dict) and m.get("url") and not is_bad_image_url(m["url"]):
                return m["url"]
    summary = str(entry.get("summary", "") or entry.get("description", ""))
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary, flags=re.I)
    if m and not is_bad_image_url(m.group(1)):
        return html.unescape(m.group(1))
    return ""


def commons_image(query):
    try:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query + " cricket",
            "gsrnamespace": "6",
            "gsrlimit": "8",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": "1200",
            "format": "json",
        }
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "VeeNewsZeroCostVideo/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        pages = list(data.get("query", {}).get("pages", {}).values())
        for page in pages:
            info = (page.get("imageinfo") or [{}])[0]
            mime = str(info.get("mime", ""))
            thumb = info.get("thumburl") or info.get("url")
            if mime.startswith("image/") and thumb and not str(thumb).lower().endswith(".svg"):
                meta = info.get("extmetadata", {})
                artist = clean(meta.get("Artist", {}).get("value", ""))[:100]
                license_name = clean(meta.get("LicenseShortName", {}).get("value", ""))
                print("COMMONS_PHOTO_OK:", page.get("title"), license_name)
                return {"url": thumb, "credit": artist or "Wikimedia Commons", "license": license_name or "Commons license"}
    except Exception as exc:
        print("Commons image search skipped:", exc)
    return None


def get_items():
    items = []
    for category, url in FEEDS.items():
        feed = feedparser.parse(url)
        for e in feed.entries[:12]:
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
            image = rss_image(e) or article_image_url(link)
            items.append({
                "title": re.sub(r"\s+-\s+[^-]+$", "", title).strip(),
                "summary": summary[:550],
                "link": link,
                "source": source,
                "image": image,
                "published": e.get("published_parsed"),
                "category": category,
            })
    return items


def choose(items):
    return items[0] if items else None


def download_image(url):
    if not url or is_bad_image_url(url):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read(8 * 1024 * 1024)
        image = Image.open(BytesIO(data)).convert("RGB")
        if image.width < 300 or image.height < 200:
            return None
        print("NEWS_PHOTO_OK:", image.size)
        return image
    except Exception as exc:
        print("News photo unavailable:", exc)
        return None


def cover(img):
    if img is None:
        return None
    ratio = max(W / img.width, H / img.height)
    nw, nh = int(img.width * ratio), int(img.height * ratio)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - W) // 2, (nh - H) // 2
    return img.crop((left, top, left + W, top + H))


def font_for(run, size, bold=False):
    path = HINDI_BOLD if bold else HINDI if any(is_hindi_char(c) for c in run) else ENG_BOLD if bold else ENG
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def runs(text):
    text = str(text or "")
    if not text:
        return []
    out, cur = [], text[0]
    cur_hi = is_hindi_char(text[0])
    for ch in text[1:]:
        hi = is_hindi_char(ch)
        if hi == cur_hi:
            cur += ch
        else:
            out.append((cur, cur_hi))
            cur, cur_hi = ch, hi
    out.append((cur, cur_hi))
    return out


def mixed_width(draw, text, size, bold=False):
    return sum(draw.textbbox((0, 0), run, font=font_for(run, size, bold))[2] for run, _ in runs(text))


def draw_mixed(draw, xy, text, size, fill, bold=False):
    x, y = xy
    for run, hi in runs(text):
        font = font_for(run, size, bold)
        draw.text((x, y), run, font=font, fill=fill, language="hi" if hi else None)
        x += draw.textbbox((0, 0), run, font=font)[2]


def wrap_mixed(draw, text, size, max_width, bold=False, max_lines=5):
    words = str(text or "").split()
    lines, current = [], ""
    for word in words:
        test = word if not current else current + " " + word
        if mixed_width(draw, test, size, bold) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines[:max_lines]


def make_base_photo(item):
    img = download_image(item["image"])
    if img:
        print("PHOTO_SOURCE: article")
        return cover(img)

    for query in ("India cricket", "cricket stadium", "cricket match"):
        fallback = commons_image(query)
        if fallback:
            print("Using Commons fallback:", fallback["credit"], fallback["license"])
            img = download_image(fallback["url"])
            if img:
                print("PHOTO_SOURCE: wikimedia")
                return cover(img)

    fallback_url = "https://commons.wikimedia.org/wiki/Special:FilePath/Rajiv%20Gandhi%20International%20Cricket%20Stadium.jpg?width=1200"
    img = download_image(fallback_url)
    if img:
        print("PHOTO_SOURCE: guaranteed-wikimedia")
        return cover(img)

    raise RuntimeError("No usable cricket photo could be downloaded.")


def make_frames(item):
    os.makedirs(WORK, exist_ok=True)
    bg = make_base_photo(item)
    if bg is None:
        # No generic Google image: use a clean cricket-themed background instead.
        bg = Image.new("RGB", (W, H), (8, 24, 65))

    title = item["title"][:190]
    summary = item["summary"] or "क्रिकेट से जुड़ी यह ताजा खबर चर्चा में है।"

    for i in range(3):
        frame = bg.copy()
        d = ImageDraw.Draw(frame, "RGBA")
        if bg.getbbox():
            # subtle dark gradient-like bands
            d.rectangle([0, 0, W, 220], fill=(5, 20, 55, 225))
            d.rectangle([0, 1470, W, H], fill=(5, 20, 55, 238))
        d.rectangle([0, 0, 18, H], fill=(221, 24, 31, 255))
        d.rounded_rectangle([42, 35, 285, 120], 18, fill=(221, 24, 31, 255))
        d.text((70, 52), "VEE NEWS", font=ImageFont.truetype(ENG_BOLD, 34), fill="white")
        d.text((325, 45), "क्रिकेट अपडेट", font=ImageFont.truetype(HINDI_BOLD, 52), fill=(255, 210, 0))

        if i == 0:
            if any(is_hindi_char(ch) for ch in title):
                title_lines = wrap_mixed(d, title, 56, 930, True, 4)
                title_font = ImageFont.truetype(HINDI_BOLD, 56)
            else:
                title_lines = []
                words = title.split()
                line = ""
                for word in words:
                    test = word if not line else line + " " + word
                    if d.textbbox((0, 0), test, font=ImageFont.truetype(ENG_BOLD, 56))[2] <= 930:
                        line = test
                    else:
                        if line:
                            title_lines.append(line)
                        line = word
                if line:
                    title_lines.append(line)
                title_lines = title_lines[:4]
                title_font = ImageFont.truetype(ENG_BOLD, 56)
            y = 1515
            for line in title_lines:
                d.text((55, y), line, font=title_font, fill="white")
                y += 72
        elif i == 1:
            draw_mixed(d, (55, 1505), "मुख्य अपडेट", 50, (255, 210, 0), True)
            lines = wrap_mixed(d, summary, 38, 930, False, 6)
            y = 1580
            for line in lines:
                if any(is_hindi_char(ch) for ch in line):
                    d.text((55, y), line, font=ImageFont.truetype(HINDI, 38), fill="white")
                else:
                    d.text((55, y), line, font=ImageFont.truetype(ENG, 38), fill="white")
                y += 55
        else:
            d.text((55, 1510), "स्रोत", font=ImageFont.truetype(HINDI_BOLD, 50), fill=(255, 210, 0))
            source_lines = wrap_mixed(d, item["source"][:55], 38, 930, False, 2)
            y = 1585
            for line in source_lines:
                d.text((55, y), line, font=ImageFont.truetype(ENG, 38), fill="white")
                y += 55
            d.text((55, 1700), "ताजा क्रिकेट खबरों के लिए", font=ImageFont.truetype(HINDI_BOLD, 38), fill="white")
            d.text((55, 1765), "FOLLOW VEE NEWS", font=ImageFont.truetype(ENG_BOLD, 38), fill=(255, 210, 0))
            d.text((55, 1845), datetime.now(IST).strftime("%d %b %Y | %H:%M IST"), font=ImageFont.truetype(ENG, 27), fill="white")

        frame.save(os.path.join(WORK, f"frame{i}.jpg"), quality=94)


def make_voice(item):
    script = (
        "नमस्कार। वी न्यूज़ पर क्रिकेट की ताज़ा खबर। "
        + item["title"] + "। "
        + (item["summary"][:320] if item["summary"] else "इस खबर से जुड़ी ताज़ा जानकारी सामने आई है।")
        + " अधिक अपडेट के लिए वी न्यूज़ को फॉलो करें।"
    )
    with open(os.path.join(WORK, "script.txt"), "w", encoding="utf-8") as f:
        f.write(script)
    gTTS(text=script, lang="hi", slow=True).save(os.path.join(WORK, "voice.mp3"))
    print("HINDI_VOICE_OK")


def make_video():
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(SCENE_SECONDS), "-i", os.path.join(WORK, "frame0.jpg"),
        "-loop", "1", "-t", str(SCENE_SECONDS), "-i", os.path.join(WORK, "frame1.jpg"),
        "-loop", "1", "-t", str(SCENE_SECONDS), "-i", os.path.join(WORK, "frame2.jpg"),
        "-i", os.path.join(WORK, "voice.mp3"),
        "-filter_complex",
        "[0:v]scale=1080:1920,setsar=1[v0];"
        "[1:v]scale=1080:1920,setsar=1[v1];"
        "[2:v]scale=1080:1920,setsar=1[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[v]",
        "-map", "[v]", "-map", "3:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
        "-c:a", "aac", "-b:a", "96k", "-pix_fmt", "yuv420p",
        "-shortest", "-movflags", "+faststart", OUT
    ]
    subprocess.run(cmd, check=True)


def main():
    items = get_items()
    item = choose(items)
    if not item:
        raise RuntimeError("No cricket news found.")
    print("Selected topic:", item["title"])
    print("Source:", item["source"])
    print("RSS/article image found:", bool(item["image"]))
    make_frames(item)
    make_voice(item)
    make_video()
    print("VIDEO_CREATED:", OUT)


if __name__ == "__main__":
    main()
