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

title = re.sub(r"\s+", " ", unicodedata.normalize("NFC", title)).strip()
source = re.sub(r"\s+", " ", unicodedata.normalize("NFC", source)).strip()

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
ENGLISH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

WHITE = (255, 255, 255)
BLACK = (15, 25, 45)
RED = (210, 15, 25)
BLUE = (10, 48, 125)
GREY = (100, 115, 135)


def f(path, size):
    return ImageFont.truetype(path, size)


def mixed_width(text, size, bold=False):
    hf = f(HINDI_BOLD if bold else HINDI, size)
    ef = f(ENGLISH_BOLD, size)
    width = 0
    for ch in text:
        ff = hf if 0x0900 <= ord(ch) <= 0x097F else ef
        b = draw.textbbox((0, 0), ch, font=ff)
        width += b[2] - b[0]
    return width


def draw_mixed(x, y, text, size, fill, bold=False):
    hf = f(HINDI_BOLD if bold else HINDI, size)
    ef = f(ENGLISH_BOLD, size)
    current = ""
    current_type = None
    pos = x

    def flush(segment, kind, xpos):
        if not segment:
            return xpos
        ff = hf if kind == "h" else ef
        draw.text((xpos, y), segment, font=ff, fill=fill)
        return draw.textbbox((xpos, y), segment, font=ff)[2]

    for ch in text:
        kind = "h" if 0x0900 <= ord(ch) <= 0x097F else "e"
        if current_type is not None and kind != current_type:
            pos = flush(current, current_type, pos)
            current = ""
        current += ch
        current_type = kind
    flush(current, current_type, pos)


def wrap(text, size, max_width, max_lines=4):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = word if not current else current + " " + word
        if mixed_width(test, size, True) <= max_width:
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
    while mixed_width(last + "...", size, True) > max_width and len(last) > 4:
        last = last[:-1]
    lines[-1] = last.rstrip() + "..."
    return lines

# Header
header_h = 145
draw.rectangle([0, 0, WIDTH, header_h], fill=BLUE)
draw.text((315, 24), "Veena News", fill=WHITE, font=f(ENGLISH_BOLD, 42))
draw.text((315, 82), "ब्रेकिंग खबर", fill=WHITE, font=f(HINDI_BOLD, 24))

# Main white card
draw.rounded_rectangle([35, 160, 1165, 755], radius=16, fill=WHITE)

# Breaking banner
draw.rounded_rectangle([190, 155, 1010, 250], radius=18, fill=RED)
banner = "🚨  BREAKING NEWS"
# Emoji is intentionally replaced by plain text because fonts may not support it.
banner = "BREAKING NEWS"
bw = mixed_width(banner, 50, True)
draw_mixed((600 - bw // 2, 175), banner, 50, WHITE, True)

# Accent lines
for x in (145, 172):
    draw.polygon([(x, 170), (x + 22, 170), (x - 2, 235), (x - 24, 235)], fill=BLUE)
for x in (1030, 1057):
    draw.polygon([(x, 170), (x + 22, 170), (x + 46, 235), (x + 24, 235)], fill=BLUE)

# Headline
max_width = 980
size = 46
while size > 30 and len(wrap(title, size, max_width, 4)) > 4:
    size -= 2
lines = wrap(title, size, max_width, 4)
line_h = size + 14
start_y = 305
for i, line in enumerate(lines):
    w = mixed_width(line, size, True)
    draw_mixed((600 - w // 2, start_y + i * line_h), line, size, BLACK, True)

# Source
if source:
    source_text = "स्रोत: " + source
    if mixed_width(source_text, 24, False) > 900:
        source_text = source_text[:60] + "..."
    sw = mixed_width(source_text, 24, False)
    draw_mixed((600 - sw // 2, 555), source_text, 24, GREY, False)

# Footer
draw.line([(70, 670), (1130, 670)], fill=BLUE, width=3)
draw.text((70, 690), "Veena News", fill=BLUE, font=f(ENGLISH_BOLD, 25))
draw.text((850, 695), "#VeenaNews   #BreakingNews   #HindiNews", fill=BLUE, font=f(ENGLISH_BOLD, 18))

canvas.save(OUTPUT, quality=95, optimize=True)
print(f"Breaking image created: {OUTPUT}")
