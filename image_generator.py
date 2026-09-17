from PIL import Image, ImageDraw, ImageFont
import sys
import os

headlines_text = sys.argv[1]

headlines = [
    line.strip()
    for line in headlines_text.split("\n")
    if line.strip()
][:10]


# ==============================
# VEENA NEWS BACKGROUND
# ==============================

BACKGROUND = "veena news background.jpg"

if not os.path.exists(BACKGROUND):
    raise FileNotFoundError(
        f"Background image not found: {BACKGROUND}"
    )

background = Image.open(BACKGROUND).convert("RGB")

# Background का पूरा design सुरक्षित रखते हुए resize
WIDTH = 1200
HEIGHT = 800

background.thumbnail(
    (WIDTH, HEIGHT),
    Image.Resampling.LANCZOS
)

canvas = Image.new(
    "RGB",
    (WIDTH, HEIGHT),
    "white"
)

x = (WIDTH - background.width) // 2
y = (HEIGHT - background.height) // 2

canvas.paste(background, (x, y))

draw = ImageDraw.Draw(canvas)


# ==============================
# FONTS
# ==============================

HINDI_BOLD = (
    "/usr/share/fonts/truetype/noto/"
    "NotoSansDevanagari-Bold.ttf"
)

HINDI_REGULAR = (
    "/usr/share/fonts/truetype/noto/"
    "NotoSansDevanagari-Regular.ttf"
)

ENGLISH_BOLD = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)

font_title = ImageFont.truetype(
    HINDI_BOLD,
    28
)

font_headline = ImageFont.truetype(
    HINDI_REGULAR,
    21
)

font_number = ImageFont.truetype(
    ENGLISH_BOLD,
    20
)


# ==============================
# TITLE
# ==============================

draw.text(
    (95, 265),
    "आज की 10 बड़ी खबरें",
    fill="black",
    font=font_title
)


# ==============================
# HEADLINES
# ==============================

start_y = 315
line_height = 42

for index, headline in enumerate(
    headlines,
    start=1
):

    # ज्यादा लंबी headline को छोटा करें
    if len(headline) > 82:
        headline = headline[:79] + "..."

    number = f"{index}."

    draw.text(
        (65, start_y),
        number,
        fill="black",
        font=font_number
    )

    draw.text(
        (105, start_y),
        headline,
        fill="black",
        font=font_headline
    )

    start_y += line_height


# ==============================
# SAVE
# ==============================

canvas.save(
    "news_image.jpg",
    quality=95
)

print(
    f"News image created with {len(headlines)} headlines."
)
