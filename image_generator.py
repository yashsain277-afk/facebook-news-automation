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
WIDTH, HEIGHT = 1200, 900

if not os.path.exists(BACKGROUND):
    raise FileNotFoundError(f"Background image not found: {BACKGROUND}")

background = Image.open(BACKGROUND).convert("RGB")
background = ImageOps.fit(
    background,
    (WIDTH, HEIGHT),
    method=Image.Resampling.LANCZOS,
    centering=(0.5, 0.5),
)
canvas = background.copy()
draw = ImageDraw.Draw(canvas)

HINDI = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
ENGLISH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ENGLISH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


WHITE = (255, 255, 255)
BLACK = (15, 25, 45)
RED = (218, 20, 28)
BLUE = (10, 48, 125)
LIGHT_BLUE = (205, 220, 238)
SOURCE = (95, 120, 155)


def is_hindi(char):
    code = ord(char)
    return 0x0900 <= code <= 0x097F


def is_ascii_letter(char):
    return ("A" <= char <= "Z") or ("a" <= char <= "z")


def is_number(char):
    return "0" <= char <= "9"


def is_allowed_punctuation(char):
    return char in " .,।!?;:-–—()/₹'%+&@#*"


def sanitize_text(text):
    """Keep only characters supported by the fonts; remove emojis/garbled glyphs."""
    text = unicodedata.normalize("NFC", str(text))
    cleaned = []
    for char in text:
        if (
            is_hindi(char)
            or is_ascii_letter(char)
            or is_number(char)
            or is_allowed_punctuation(char)
        ):
            cleaned.append(char)
        else:
            cleaned.append(" ")
    return re.sub(r"\s+", " ", "".join(cleaned)).strip()


def draw_mixed_text(xy, text, size, fill, bold=False):
    """Render Hindi with Noto Devanagari and English/numbers with DejaVu."""
    x, y = xy
    text = sanitize_text(text)
    if not text:
        return

    hindi_font = font(HINDI_BOLD if bold else HINDI, size)
    english_font = font(ENGLISH_BOLD if bold else ENGLISH, size)

    current_type = None
    current_text = ""
    current_x = x

    def flush(segment, segment_type, x_pos):
        if not segment:
            return x_pos
        segment_font = hindi_font if segment_type == "hindi" else english_font
        draw.text((x_pos, y), segment, font=segment_font, fill=fill)
        box = draw.textbbox((x_pos, y), segment, font=segment_font)
        return box[2]

    for char in text:
        char_type = "hindi" if is_hindi(char) else "english"
        if current_type is not None and char_type != current_type:
            current_x = flush(current_text, current_type, current_x)
            current_text = ""
        current_text += char
        current_type = char_type

    flush(current_text, current_type, current_x)


def mixed_text_width(text, size, bold=False):
    text = sanitize_text(text)
    if not text:
        return 0
    hindi_font = font(HINDI_BOLD if bold else HINDI, size)
    english_font = font(ENGLISH_BOLD if bold else ENGLISH, size)
    width = 0
    for char in text:
        fnt = hindi_font if is_hindi(char) else english_font
        box = draw.textbbox((0, 0), char, font=fnt)
        width += box[2] - box[0]
    return width


def shorten(text, size, max_width, bold=True):
    text = sanitize_text(text)
    if mixed_text_width(text, size, bold) <= max_width:
        return text

    suffix = "..."
    result = ""
    for word in text.split():
        candidate = word if not result else result + " " + word
        if mixed_text_width(candidate + suffix, size, bold) <= max_width:
            result = candidate
        else:
            break

    if result:
        return result + suffix

    chars = ""
    for char in text:
        if mixed_text_width(chars + char + suffix, size, bold) <= max_width:
            chars += char
        else:
            break
    return (chars or text[:10]) + suffix


# Header
# Use the supplied HS News Times header artwork.
HEADER_IMAGE = "hs_news_header.png"
if not os.path.exists(HEADER_IMAGE):
    raise FileNotFoundError(f"Header image not found: {HEADER_IMAGE}. The workflow converts hs_news_header.webp to PNG before running.")
header = Image.open(HEADER_IMAGE).convert("RGB")
header = header.resize((WIDTH, 283), Image.Resampling.LANCZOS)
canvas.paste(header, (0, 0))

# Main white panel
draw.rounded_rectangle([30, 300, 1170, 890], radius=12, fill=WHITE)

# Red title banner
draw.rounded_rectangle([190, 290, 1010, 390], radius=18, fill=RED)
for x in (145, 172):
    draw.polygon(
        [(x, 305), (x + 22, 305), (x - 2, 373), (x - 24, 373)],
        fill=BLUE,
    )
for x in (1030, 1057):
    draw.polygon(
        [(x, 305), (x + 22, 305), (x + 46, 373), (x + 24, 373)],
        fill=BLUE,
    )

title = "आज की 10 बड़ी खबरें"
title_font_size = 54
title_width = mixed_text_width(title, title_font_size, bold=True)
draw_mixed_text(
    ((190 + 1010 - title_width) // 2, 306),
    title,
    title_font_size,
    WHITE,
    bold=True,
)

# Ten compact headline rows.
headline_size = 24
source_size = 16
number_font = font(ENGLISH_BOLD, 22)
NUMBER_X = 108
TEXT_X = 160
TEXT_RIGHT = 1135
START_Y = 410
ROW_HEIGHT = 43

for index in range(10):
    y = START_Y + index * ROW_HEIGHT

    draw.ellipse(
        [NUMBER_X - 22, y - 2, NUMBER_X + 22, y + 42],
        fill=RED,
    )

    number = str(index + 1)
    nb = draw.textbbox((0, 0), number, font=number_font)
    nw, nh = nb[2] - nb[0], nb[3] - nb[1]
    draw.text(
        (NUMBER_X - nw // 2, y + 5 - nh // 2 + 8),
        number,
        fill=WHITE,
        font=number_font,
    )

    if index < len(items):
        title_text = sanitize_text(items[index]["title"])
        source_text = sanitize_text(items[index]["source"])

        # Source gets its own small area so it can never overlap the headline.
        source_display = f" | {source_text}" if source_text else ""
        if source_display:
            source_display = shorten(source_display, source_size, 220, bold=False)

        source_width = mixed_text_width(source_display, source_size, bold=False)
        title_max_width = TEXT_RIGHT - TEXT_X - source_width - 18
        title_display = shorten(title_text, headline_size, max(420, title_max_width), bold=True)

        draw_mixed_text(
            (TEXT_X, y + 1),
            title_display,
            headline_size,
            BLACK,
            bold=True,
        )

        if source_display:
            title_width = mixed_text_width(title_display, headline_size, bold=True)
            source_x = min(
                TEXT_X + title_width + 10,
                TEXT_RIGHT - source_width,
            )
            draw_mixed_text(
                (source_x, y + 6),
                source_display,
                source_size,
                SOURCE,
                bold=False,
            )

    draw.line(
        [(TEXT_X, y + 44), (TEXT_RIGHT, y + 44)],
        fill=LIGHT_BLUE,
        width=1,
    )

# Footer
draw.line([(70, 705), (1130, 705)], fill=BLUE, width=3)
footer_font = font(ENGLISH_BOLD, 25)
draw.text((70, 855), "HS News Times", fill=BLUE, font=footer_font)
hashtags = "#HSNewsTimes   #HindiNews   #LocalNews"
hb = draw.textbbox((0, 0), hashtags, font=footer_font)
hw = hb[2] - hb[0]
draw.text((1130 - hw, 858), hashtags, fill=BLUE, font=font(ENGLISH_BOLD, 18))

canvas.save(OUTPUT, quality=95, optimize=True)
print(f"Final HS News Times template image created: {OUTPUT}")
