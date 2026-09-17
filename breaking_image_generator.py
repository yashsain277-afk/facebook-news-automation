from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import re
import sys
import unicodedata

if len(sys.argv) < 2:
    raise ValueError("Breaking headline input नहीं मिला")

raw = sys.argv[1]
if " || " in raw:
    title, source = raw.split(" || ", 1)
else:
    title, source = raw, ""


def clean_text(text):
    text = unicodedata.normalize("NFC", str(text))
    allowed = []
    for ch in text:
        code = ord(ch)
        if (
            0x0900 <= code <= 0x097F
            or "A" <= ch <= "Z"
            or "a" <= ch <= "z"
            or "0" <= ch <= "9"
            or ch in " .,:;!?%₹()/-–—'\"+&#@"
        ):
            allowed.append(ch)
        else:
            allowed.append(" ")
    return re.sub(r"\s+", " ", "".join(allowed)).strip()


title = clean_text(title)
source = clean_text(source)

WIDTH, HEIGHT = 1200, 800
BACKGROUND = "veena news background.jpg"
OUTPUT = "breaking_news_image.jpg"

if not os.path.exists(BACKGROUND):
    raise FileNotFoundError(f"Background image not found: {BACKGROUND}")

bg = Image.open(BACKGROUND).convert("RGB")
bg = ImageOps.fit(bg, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
canvas = bg.copy()
draw = ImageDraw.Draw(canvas)

HINDI = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"

if not os.path.exists(HINDI):
    raise FileNotFoundError(f"Hindi font not found: {HINDI}")
if not os.path.exists(HINDI_BOLD):
    raise FileNotFoundError(f"Hindi bold font not found: {HINDI_BOLD}")

WHITE = (255, 255, 255)
BLACK = (15, 25, 45)
RED = (210, 15, 25)
BLUE = (10, 48, 125)
GREY = (100, 115, 135)


def font(size, bold=False):
    return ImageFont.truetype(HINDI_BOLD if bold else HINDI, size)


def text_width(text, size, bold=False):
    box = draw.textbbox((0, 0), text, font=font(size, bold))
    return box[2] - box[0]


def wrap(text, size, max_width, max_lines=4):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = word if not current else current + " " + word
        if text_width(test, size, True) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    if len(lines) <= max_lines:
        return lines

    lines = lines[:max_lines]
    last = lines[-1]
    while text_width(last + "...", size, True) > max_width and len(last) > 4:
        last = last[:-1]
    lines[-1] = last.rstrip() + "..."
    return lines


# Header
draw.rectangle([0, 0, WIDTH, 145], fill=BLUE)
draw.text((315, 22), "Veena News", fill=WHITE, font=font(42, True))
draw.text((315, 82), "ब्रेकिंग खबर", fill=WHITE, font=font(24, True))

# Main card
draw.rounded_rectangle([35, 160, 1165, 755], radius=16, fill=WHITE)

# Breaking banner
draw.rounded_rectangle([190, 155, 1010, 250], radius=18, fill=RED)
banner = "BREAKING NEWS"
bw = text_width(banner, 48, True)
draw.text((600 - bw // 2, 176), banner, fill=WHITE, font=font(48, True))

# Blue accents
for x in (145, 172):
    draw.polygon([(x, 170), (x + 22, 170), (x - 2, 235), (x - 24, 235)], fill=BLUE)
for x in (1030, 1057):
    draw.polygon([(x, 170), (x + 22, 170), (x + 46, 235), (x + 24, 235)], fill=BLUE)

# Headline
max_width = 980
size = 46
lines = wrap(title, size, max_width, 4)
while len(lines) > 4 and size > 28:
    size -= 2
    lines = wrap(title, size, max_width, 4)

line_height = size + 14
start_y = 300
for i, line in enumerate(lines):
    w = text_width(line, size, True)
    draw.text((600 - w // 2, start_y + i * line_height), line, fill=BLACK, font=font(size, True))

# Source
if source:
    source_text = "स्रोत: " + source
    while text_width(source_text, 22, False) > 900 and len(source) > 10:
        source = source[:-4].rstrip(" .") + "..."
        source_text = "स्रोत: " + source
    sw = text_width(source_text, 22, False)
    draw.text((600 - sw // 2, 555), source_text, fill=GREY, font=font(22, False))

# Footer
draw.line([(70, 670), (1130, 670)], fill=BLUE, width=3)
draw.text((70, 690), "Veena News", fill=BLUE, font=font(25, True))
footer = "#VeenaNews   #BreakingNews   #HindiNews"
fw = text_width(footer, 18, True)
draw.text((1130 - fw, 695), footer, fill=BLUE, font=font(18, True))

canvas.save(OUTPUT, quality=95, optimize=True)
print(f"Breaking image created: {OUTPUT}")
