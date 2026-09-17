from PIL import Image, ImageDraw, ImageFont, ImageOps
import sys
import os


# ==========================================
# INPUT
# ==========================================

headlines_text = sys.argv[1]

headlines = [
    line.strip()
    for line in headlines_text.split("\n")
    if line.strip()
][:10]


# ==========================================
# FILES
# ==========================================

BACKGROUND = "veena news background.jpg"

if not os.path.exists(BACKGROUND):
    raise FileNotFoundError(
        f"Background image not found: {BACKGROUND}"
    )


# ==========================================
# CANVAS
# ==========================================

WIDTH = 1200
HEIGHT = 800

background = Image.open(BACKGROUND).convert("RGB")

# Background को पूरा canvas cover करवाएं
background = ImageOps.fit(
    background,
    (WIDTH, HEIGHT),
    method=Image.Resampling.LANCZOS,
    centering=(0.5, 0.5)
)

canvas = background.copy()

draw = ImageDraw.Draw(canvas)


# ==========================================
# FONTS
# ==========================================

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


# ==========================================
# FONT FUNCTION
# ==========================================

def get_font(path, size):
    return ImageFont.truetype(path, size)


# ==========================================
# HEADLINE FIT FUNCTION
# ==========================================

def fit_headline(text, max_width):
    """
    Headline को available width में fit करता है।
    Font size automatically कम होगा।
    """

    max_size = 22
    min_size = 14

    for size in range(max_size, min_size - 1, -1):

        font = get_font(
            HINDI_REGULAR,
            size
        )

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=font
        )

        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            return text, font

    # अगर फिर भी बहुत लंबी है
    font = get_font(
        HINDI_REGULAR,
        min_size
    )

    shortened = text

    while len(shortened) > 10:

        bbox = draw.textbbox(
            (0, 0),
            shortened + "...",
            font=font
        )

        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            return shortened + "...", font

        shortened = shortened[:-1]

    return shortened + "...", font


# ==========================================
# TITLE
# ==========================================

title_font = get_font(
    HINDI_BOLD,
    27
)

draw.text(
    (70, 270),
    "आज की 10 बड़ी खबरें",
    fill="black",
    font=title_font
)


# ==========================================
# HEADLINES AREA
# ==========================================

START_Y = 315

NUMBER_X = 55
TEXT_X = 105

MAX_TEXT_WIDTH = 1030

LINE_HEIGHT = 32


# ==========================================
# DRAW 10 HEADLINES
# ==========================================

for index, headline in enumerate(
    headlines,
    start=1
):

    # Headline को available width में fit करें
    headline, headline_font = fit_headline(
        headline,
        MAX_TEXT_WIDTH
    )

    number_font = get_font(
        ENGLISH_BOLD,
        17
    )

    # Number
    draw.text(
        (NUMBER_X, START_Y),
        f"{index}.",
        fill="black",
        font=number_font
    )

    # Headline
    draw.text(
        (TEXT_X, START_Y),
        headline,
        fill="black",
        font=headline_font
    )

    # Divider
    divider_y = START_Y + 28

    draw.line(
        [
            (50, divider_y),
            (1150, divider_y)
        ],
        fill="gray",
        width=1
    )

    START_Y += LINE_HEIGHT


# ==========================================
# FOOTER
# ==========================================

footer_font = get_font(
    ENGLISH_BOLD,
    16
)

draw.text(
    (45, 690),
    "Veena News",
    fill="black",
    font=footer_font
)


# ==========================================
# SAVE IMAGE
# ==========================================

canvas.save(
    "news_image.jpg",
    quality=95,
    optimize=True
)


print(
    f"News image created with {len(headlines)} headlines."
)
