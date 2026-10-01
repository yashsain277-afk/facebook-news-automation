import feedparser, json, os, re, html, requests, textwrap
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote
import subprocess

PAGE_ID=os.environ["FB_PAGE_ID"]; TOKEN=os.environ["FB_PAGE_ACCESS_TOKEN"]
POSTED_FILE="siyast_posted.json"

FEEDS=[
("राष्ट्रीय राजनीति","https://news.google.com/rss/search?q=India+politics+Parliament+government+political+parties&hl=hi&gl=IN&ceid=IN:hi"),
("प्रधानमंत्री और केंद्र","https://news.google.com/rss/search?q=India+Prime+Minister+central+government+politics+India&hl=hi&gl=IN&ceid=IN:hi"),
("विपक्ष और संसद","https://news.google.com/rss/search?q=India+opposition+Parliament+politics+India&hl=hi&gl=IN&ceid=IN:hi"),
("राज्य राजनीति","https://news.google.com/rss/search?q=India+Indian+state+politics+Chief+Minister+politics&hl=hi&gl=IN&ceid=IN:hi"),
]

try: posted=json.load(open(POSTED_FILE,encoding="utf-8"))
except: posted=[]

items=[]
for category,url in FEEDS:
    feed=feedparser.parse(url)
    for e in feed.entries[:15]:
        title=html.unescape(re.sub(r"\s+"," ",e.get("title","")).strip())
        if not title or title in posted: continue
        dt=datetime.min.replace(tzinfo=timezone.utc)
        if e.get("published_parsed"): dt=datetime(*e.published_parsed[:6],tzinfo=timezone.utc)
        summary=html.unescape(re.sub(r"<[^>]+>"," ",e.get("summary","")))
        summary=re.sub(r"\s+"," ",summary).strip()
        source=e.get("source",{}).get("title","") or "News source"
        link=e.get("link","")
        media_url = None
        media = e.get("media_content") or e.get("media_thumbnail") or []
        if media and isinstance(media, list):
            media_url = media[0].get("url")
        items.append((dt,category,title,summary,source,link,media_url))

items.sort(key=lambda x:x[0],reverse=True)
if not items:
    raise SystemExit("No new Indian political story found. Try the workflow again later.")
_,category,title,summary,source,link,news_image_url=items[0]

# Google News often appends the publisher domain to the title.
# Keep the headline itself clean; show the publisher separately in the source line.
title = re.sub(r"\s+-\s*[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", "", title).strip()

# Rewrite the news into a concise caption of about 100 words.
# Keep only facts present in the title/available RSS summary; do not add
# generic political commentary or invented details.
def rewrite_to_100_words(title, summary):
    raw = f"{title}. {summary}"
    raw = html.unescape(raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"https?://\\S+", " ", raw)
    raw = re.sub(r"\\s+", " ", raw).strip()

    # Prefer complete sentences. If the source is shorter, use all available text.
    sentences = re.split(r"(?<=[.!?।])\\s+", raw)
    selected = []
    count = 0
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        if count + len(words) <= 100:
            selected.append(sentence)
            count += len(words)
        else:
            remaining = 100 - count
            if remaining > 0:
                selected.append(" ".join(words[:remaining]))
                count = 100
            break

    result = " ".join(selected).strip()
    return result

news_rewrite = rewrite_to_100_words("", summary)
# Remove a leading copy of the headline if the RSS summary repeats it.
news_rewrite = re.sub(
    r"^" + re.escape(title) + r"[s.:,-]*",
    "",
    news_rewrite,
    flags=re.IGNORECASE
).strip()

caption_parts = [
    f"📰 सियासत | {title}",
    news_rewrite,
    f"📚 संदर्भ / Reference: {source}",
    f"🔗 मूल समाचार: {link}",
    "#Siyasat #IndianPolitics #Bharat #PoliticalNews",
]
caption = "\n\n".join(p for p in caption_parts if p)


# Use the single saved Siyasat template image on every post.
# No leader photos are downloaded and no new base image is generated.
TEMPLATE_FILE = "siyast_template.jpg"

W, H = 1200, 800
im = Image.open(TEMPLATE_FILE).convert("RGB")

# Replace only the headline area of the saved template.
# The permanent faces, Parliament, party symbols, branding and overall design remain unchanged.
d = ImageDraw.Draw(im)

def find_hindi_font(style):
    # Use the exact Noto Sans Devanagari files first. This avoids fc-match
    # selecting an unrelated fallback font on GitHub Actions.
    exact = {
        # UI variants have broader fallback coverage for mixed Hindi/English
        # text and are safer for social-media headline rendering.
        "Bold": "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Bold.ttf",
        "Regular": "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
    }
    if os.path.isfile(exact[style]):
        return exact[style]

    # Secondary fallback for environments where the font is installed elsewhere.
    for pattern in (f"Noto Sans Devanagari:style={style}", "Noto Sans Devanagari"):
        try:
            path = subprocess.check_output(
                ["fc-match", "-f", "%{file}", pattern],
                text=True
            ).strip()
            if path and os.path.isfile(path):
                return path
        except Exception:
            pass

    raise RuntimeError("Noto Sans Devanagari font is not installed")

font_bold = find_hindi_font("Bold")
font_reg = find_hindi_font("Regular")

def find_latin_font(style):
    exact = {
        "Bold": "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "Regular": "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    }
    if os.path.isfile(exact[style]):
        return exact[style]
    for pattern in (f"Noto Sans:style={style}", "Noto Sans", "DejaVu Sans"):
        try:
            path = subprocess.check_output(
                ["fc-match", "-f", "%{file}", pattern],
                text=True
            ).strip()
            if path and os.path.isfile(path):
                return path
        except Exception:
            pass
    raise RuntimeError("Latin font is not installed")

latin_bold = find_latin_font("Bold")

def fit_font(path, size):
    try:
        return ImageFont.truetype(
            path, size,
            layout_engine=ImageFont.Layout.RAQM
        )
    except (AttributeError, ValueError):
        return ImageFont.truetype(path, size)

# IMPORTANT: the news title is often English, while the Siyasat label is Hindi.
# Using a Devanagari-only font for an English title produces □□□ glyph boxes.
f_head_hi = fit_font(font_bold, 38)
f_head_en = fit_font(latin_bold, 38)
f_sub = fit_font(font_bold, 27)

def has_devanagari(text):
    return any("\u0900" <= ch <= "\u097f" for ch in text)

def font_for_text(text, size=38):
    # Use the UI Devanagari font for any line containing Hindi.
    # It also contains Latin glyphs, so mixed headlines stay consistent.
    return fit_font(font_bold if has_devanagari(text) else latin_bold, size)

# Right-side headline block in the saved 1200x800 template.
# Cover the old baked-in headline, then redraw the new headline in the same style.
d.rectangle((690, 382, 1190, 585), fill=(248, 248, 245))
d.rectangle((690, 475, 1190, 558), fill=(215, 30, 30))
d.rectangle((690, 558, 1190, 620), fill=(242, 195, 0))

headline = re.sub(r"\s+", " ", title).strip()

# The headline box is only ~480px wide. Choose wrapping and font size
# dynamically so long English headlines never run outside the template.
def make_headline_lines(text):
    for width in (31, 34, 37, 40):
        lines = textwrap.wrap(
            text,
            width=width,
            break_long_words=False,
            break_on_hyphens=False
        )
        if len(lines) <= 4:
            return lines
    return textwrap.wrap(
        text,
        width=37,
        break_long_words=True,
        break_on_hyphens=True
    )[:4]

headline_lines = make_headline_lines(headline)

def fit_headline_font(line, max_size=34, min_size=22):
    size = max_size
    while size >= min_size:
        font = font_for_text(line, size)
        box = d.textbbox((0, 0), line, font=font)
        if box[2] - box[0] <= 465:
            return font
        size -= 1
    return font_for_text(line, min_size)

# Two lines on white, up to two lines on red.
y = 397
for line in headline_lines[:2]:
    font = fit_headline_font(line)
    d.text((710, y), line, font=font, fill=(10, 10, 10))
    y += 40

remaining = headline_lines[2:]
if remaining:
    y = 483
    for line in remaining[:2]:
        font = fit_headline_font(line)
        d.text((710, y), line, font=font, fill=(255, 255, 255))
        y += 40

d.text((715, 570), "सियासत • ताज़ा राजनीतिक अपडेट", font=f_sub, fill=(20, 20, 20))

im.save("siyast_post.jpg", quality=92, optimize=True)

with open("siyast_post.jpg", "rb") as f:
    r = requests.post(
        f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos",
        data={"caption": caption, "access_token": TOKEN},
        files={"source": ("siyast_post.jpg", f, "image/jpeg")},
        timeout=90
    )
print("Facebook:", r.status_code, r.text)
r.raise_for_status()

posted.append(title)
json.dump(
    posted[-300:],
    open(POSTED_FILE, "w", encoding="utf-8"),
    ensure_ascii=False,
    indent=2
)
