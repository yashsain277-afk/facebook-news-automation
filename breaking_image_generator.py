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

# Instagram / WhatsApp vertical format: 1080 x 1920 (9:16)
WIDTH, HEIGHT = 1080, 1920
BACKGROUND = "veena news background.jpg"
OUTPUT = "breaking_news_image.jpg"

if not os.path.exists(BACKGROUND):
    raise FileNotFoundError(f"Background image not found: {BACKGROUND}")

bg = Image.open(BACKGROUND).convert("RGB")
bg = ImageOps.fit(
    bg,
    (WIDTH, HEIGHT),
    method=Image.Resampling.LANCZOS,
    centering=(0.5, 0.5),
)
canvas = bg.copy()
draw = ImageDraw.Draw(canvas)

HINDI = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
LATIN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
LATIN_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

for path, label in (
    (HINDI, "Hindi regular font"),
    (HINDI_BOLD, "Hindi bold font"),
    (LATIN, "Latin regular font"),
    (LATIN_BOLD, "Latin bold font"),
):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{label} not found: {path}")

WHITE = (255, 255, 255)
BLACK = (15, 25, 45)
RED = (215, 15, 25)
BLUE = (10, 48, 125)
GREY = (95, 105, 120)
LIGHT = (238, 242, 248)


def font(size, bold=False, hindi=False):
    if hindi:
        return ImageFont.truetype(HINDI_BOLD if bold else HINDI, size)
    return ImageFont.truetype(LATIN_BOLD if bold else LATIN, size)


def is_hindi_char(ch):
    return 0x0900 <= ord(ch) <= 0x097F


def text_runs(text):
    """Split text into Devanagari and non-Devanagari runs."""
    if not text:
        return []

    runs = []
    current = text[0]
    current_hindi = is_hindi_char(text[0])

    for ch in text[1:]:
        ch_hindi = is_hindi_char(ch)
        if ch_hindi == current_hindi:
            current += ch
        else:
            runs.append((current, current_hindi))
            current = ch
            current_hindi = ch_hindi

    runs.append((current, current_hindi))
    return runs


def mixed_text_width(text, size, bold=False):
    total = 0
    for run, hindi in text_runs(text):
        box = draw.textbbox((0, 0), run, font=font(size, bold, hindi))
        total += box[2] - box[0]
    return total


def draw_mixed_text(text, x, y, size, fill, bold=False):
    cursor_x = x
    for run, hindi in text_runs(text):
        fnt = font(size, bold, hindi)
        draw.text((cursor_x, y), run, fill=fill, font=fnt)
        box = draw.textbbox((cursor_x, y), run, font=fnt)
        cursor_x = box[2]
    return cursor_x


def wrap(text, size, max_width, max_lines=7):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else current + " " + word
        if mixed_text_width(test, size, True) <= max_width:
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
    while mixed_text_width(last + "...", size, True) > max_width and len(last) > 4:
        last = last[:-1]
    lines[-1] = last.rstrip() + "..."
    return lines


def centered_text(text, y, size, fill, bold=False):
    w = mixed_text_width(text, size, bold)
    draw_mixed_text(text, WIDTH // 2 - w // 2, y, size, fill, bold)


# ---------------- Header ----------------
HEADER_BOTTOM = 250
draw.rectangle([0, 0, WIDTH, HEADER_BOTTOM], fill=BLUE)

centered_text("Veena News", 38, 68, WHITE, True)
centered_text("सच्ची खबर  |  हर समय  |  आपके साथ", 132, 30, WHITE, True)
centered_text("आज की बड़ी खबर", 185, 28, WHITE, True)

# ---------------- Main white card ----------------
CARD_LEFT = 45
CARD_TOP = 275
CARD_RIGHT = WIDTH - 45
CARD_BOTTOM = 1710

draw.rounded_rectangle(
    [CARD_LEFT, CARD_TOP, CARD_RIGHT, CARD_BOTTOM],
    radius=28,
    fill=WHITE,
)

# ---------------- Breaking banner ----------------
BANNER_LEFT = 70
BANNER_TOP = 315
BANNER_RIGHT = WIDTH - 70
BANNER_BOTTOM = 510

draw.rounded_rectangle(
    [BANNER_LEFT, BANNER_TOP, BANNER_RIGHT, BANNER_BOTTOM],
    radius=28,
    fill=RED,
)

centered_text("BREAKING NEWS", 355, 76, WHITE, True)

# Blue decorative bars
for x in (82, 112):
    draw.polygon(
        [(x, 335), (x + 25, 335), (x - 5, 490), (x - 30, 490)],
        fill=BLUE,
    )
for x in (968, 998):
    draw.polygon(
        [(x, 335), (x + 25, 335), (x + 55, 490), (x + 30, 490)],
        fill=BLUE,
    )

# ---------------- Headline ----------------
TEXT_LEFT = 95
TEXT_RIGHT = WIDTH - 95
MAX_WIDTH = TEXT_RIGHT - TEXT_LEFT

size = 58
lines = wrap(title, size, MAX_WIDTH, 7)
while len(lines) > 7 and size > 40:
    size -= 2
    lines = wrap(title, size, MAX_WIDTH, 7)

line_height = size + 24
headline_height = len(lines) * line_height
start_y = 570

for i, line in enumerate(lines):
    w = mixed_text_width(line, size, True)
    draw_mixed_text(
        line,
        WIDTH // 2 - w // 2,
        start_y + i * line_height,
        size,
        BLACK,
        True,
    )

# ---------------- Source ----------------
source_y = max(1050, start_y + headline_height + 70)
draw.line(
    [(100, source_y - 25), (WIDTH - 100, source_y - 25)],
    fill=LIGHT,
    width=4,
)

if source:
    source_text = "स्रोत: " + source
    while mixed_text_width(source_text, 32, False) > 850 and len(source) > 10:
        source = source[:-5].rstrip(" .") + "..."
        source_text = "स्रोत: " + source
    centered_text(source_text, source_y, 32, GREY, False)

# ---------------- Bottom brand block ----------------
BOTTOM_TOP = 1370

draw.rounded_rectangle(
    [90, BOTTOM_TOP, WIDTH - 90, 1635],
    radius=22,
    fill=BLUE,
)
centered_text("Veena News", BOTTOM_TOP + 45, 58, WHITE, True)
centered_text("सच्ची खबर  |  हर समय  |  आपके साथ", BOTTOM_TOP + 125, 28, WHITE, True)
centered_text("#VeenaNews   #BreakingNews   #HindiNews", BOTTOM_TOP + 190, 24, WHITE, True)

# Thin footer line
draw.line(
    [(70, 1760), (WIDTH - 70, 1760)],
    fill=WHITE,
    width=5,
)
centered_text("Veena News", 1790, 34, WHITE, True)

canvas.save(OUTPUT, quality=95, optimize=True)
print(f"Breaking 9:16 image created: {OUTPUT}")
