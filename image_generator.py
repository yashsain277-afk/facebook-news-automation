from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import re
import sys
import unicodedata

if len(sys.argv) < 2:
    raise ValueError("Headlines input नहीं मिला")

raw_input = sys.argv[1]

# Input format: headline || source
items = []
for line in raw_input.split("\n"):
    line = line.strip()
    if not line:
        continue
    if " || " in line:
        title, source = line.split(" || ", 1)
    else:
        title, source = line, ""
    items.append({"title": title.strip(), "source": source.strip()})
items = items[:10]

BACKGROUND = "veena news background.jpg"
OUTPUT = "news_image.jpg"
WIDTH, HEIGHT = 1200, 800

if not os.path.exists(BACKGROUND):
    raise FileNotFoundError(f"Background image not found: {BACKGROUND}")

background = Image.open(BACKGROUND).convert("RGB")
background = ImageOps.fit(
    background, (WIDTH, HEIGHT),
    method=Image.Resampling.LANCZOS,
    centering=(0.5, 0.5),
)
canvas = background.copy()
draw = ImageDraw.Draw(canvas)

HINDI = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
ENGLISH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


WHITE = (255, 255, 255)
BLACK = (15, 25, 45)
RED = (218, 20, 28)
BLUE = (10, 48, 125)
LIGHT_BLUE = (205, 220, 238)
SOURCE = (95, 120, 155)


def clean_text(text):
    text = unicodedata.normalize("NFC", str(text))
    return re.sub(r"\s+", " ", text).strip()


def text_width(text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def shorten(text, fnt, max_width):
    text = clean_text(text)
    if text_width(text, fnt) <= max_width:
        return text
    suffix = "..."
    result = ""
    for word in text.split():
        candidate = word if not result else result + " " + word
        if text_width(candidate + suffix, fnt) <= max_width:
            result = candidate
        else:
            break
    if result:
        return result + suffix
    chars = ""
    for char in text:
        if text_width(chars + char + suffix, fnt) <= max_width:
            chars += char
        else:
            break
    return (chars or text[:10]) + suffix


# Header: clean branded area with the existing Veena News background/logo.
draw.rectangle([0, 0, WIDTH, 145], fill=BLUE)
page_font = font(ENGLISH_BOLD, 42)
tagline_font = font(HINDI, 24)
date_font = font(HINDI, 24)
draw.text((315, 24), "Veena News", fill=WHITE, font=page_font)
draw.text((315, 82), "सच्ची खबर  |  हर समय  |  आपके साथ", fill=WHITE, font=tagline_font)
draw.text((850, 82), "आज की खबरें", fill=WHITE, font=date_font)

# Main white panel
draw.rounded_rectangle([30, 165, 1170, 770], radius=12, fill=WHITE)

# Red title banner
draw.rounded_rectangle([190, 155, 1010, 255], radius=18, fill=RED)
for x in (145, 172):
    draw.polygon([(x, 170), (x + 22, 170), (x - 2, 238), (x - 24, 238)], fill=BLUE)
for x in (1030, 1057):
    draw.polygon([(x, 170), (x + 22, 170), (x + 46, 238), (x + 24, 238)], fill=BLUE)

title_font = font(HINDI_BOLD, 54)
title = "आज की 10 बड़ी खबरें"
tb = draw.textbbox((0, 0), title, font=title_font)
tw, th = tb[2] - tb[0], tb[3] - tb[1]
draw.text(((190 + 1010 - tw) // 2, (155 + 255 - th) // 2 - 5), title, fill=WHITE, font=title_font)

# Ten compact headline rows. Source is shown in a smaller muted style.
headline_font = font(HINDI_BOLD, 24)
source_font = font(HINDI, 16)
number_font = font(ENGLISH_BOLD, 22)
NUMBER_X = 108
TEXT_X = 160
TEXT_RIGHT = 1135
START_Y = 278
ROW_HEIGHT = 43

for index in range(10):
    y = START_Y + index * ROW_HEIGHT

    draw.ellipse([NUMBER_X - 22, y - 2, NUMBER_X + 22, y + 42], fill=RED)
    number = str(index + 1)
    nb = draw.textbbox((0, 0), number, font=number_font)
    nw, nh = nb[2] - nb[0], nb[3] - nb[1]
    draw.text((NUMBER_X - nw // 2, y + 5 - nh // 2 + 8), number, fill=WHITE, font=number_font)

    if index < len(items):
        title_text = clean_text(items[index]["title"])
        source_text = clean_text(items[index]["source"])
        source_display = f" | {source_text}" if source_text else ""
        source_width = text_width(source_display, source_font) if source_display else 0

        if source_width > 220:
            source_text = shorten(source_text, source_font, 210)
            source_display = f" | {source_text}"
            source_width = text_width(source_display, source_font)

        title_max_width = TEXT_RIGHT - TEXT_X - source_width - 12
        title_display = shorten(title_text, headline_font, max(420, title_max_width))
        draw.text((TEXT_X, y + 2), title_display, fill=BLACK, font=headline_font)

        if source_display:
            title_width = text_width(title_display, headline_font)
            source_x = min(TEXT_X + title_width + 10, TEXT_RIGHT - source_width)
            draw.text((source_x, y + 7), source_display, fill=SOURCE, font=source_font)

    draw.line([(TEXT_X, y + 44), (TEXT_RIGHT, y + 44)], fill=LIGHT_BLUE, width=1)

# Footer
draw.line([(70, 705), (1130, 705)], fill=BLUE, width=3)
footer_font = font(ENGLISH_BOLD, 25)
hashtag_font = font(ENGLISH_BOLD, 18)
draw.text((70, 720), "Veena News", fill=BLUE, font=footer_font)
hashtags = "#VeenaNews   #HindiNews   #News"
hb = draw.textbbox((0, 0), hashtags, font=hashtag_font)
hw = hb[2] - hb[0]
draw.text((1130 - hw, 725), hashtags, fill=BLUE, font=hashtag_font)

canvas.save(OUTPUT, quality=95, optimize=True)
print(f"Final Veena News template image created: {OUTPUT}")
