from PIL import Image, ImageDraw, ImageFont
import sys


# 10 headlines newline से आएंगी
headlines_text = sys.argv[1]

headlines = [
    line.strip()
    for line in headlines_text.split("\n")
    if line.strip()
]

# Maximum 10 headlines
headlines = headlines[:10]


WIDTH = 1200
HEIGHT = 630

image = Image.new(
    "RGB",
    (WIDTH, HEIGHT),
    "white"
)

draw = ImageDraw.Draw(image)


# Fonts
HINDI_BOLD = (
    "/usr/share/fonts/truetype/noto/"
    "NotoSansDevanagari-Bold.ttf"
)

ENGLISH_BOLD = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)


font_brand = ImageFont.truetype(
    ENGLISH_BOLD,
    30
)

font_label = ImageFont.truetype(
    ENGLISH_BOLD,
    26
)

font_headline = ImageFont.truetype(
    HINDI_BOLD,
    25
)


# =========================
# TOP HEADER
# =========================

draw.rectangle(
    [(0, 0), (WIDTH, 85)],
    fill="black"
)

draw.text(
    (45, 24),
    "VEENA NEWS",
    fill="white",
    font=font_brand
)


# =========================
# LABELS
# =========================

draw.text(
    (45, 105),
    "BREAKING NEWS",
    fill="black",
    font=font_label
)

draw.text(
    (45, 140),
    "HEADLINES",
    fill="black",
    font=font_label
)


# =========================
# HEADLINES
# =========================

start_y = 185
line_height = 42

max_width = 1090


def fit_text(text, font, max_width):

    # पहले पूरा text check करें
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    width = bbox[2] - bbox[0]

    if width <= max_width:
        return text

    # लंबी headline को छोटा करें
    shortened = text

    while len(shortened) > 10:

        shortened = shortened[:-1]

        test_text = shortened + "..."

        bbox = draw.textbbox(
            (0, 0),
            test_text,
            font=font
        )

        width = bbox[2] - bbox[0]

        if width <= max_width:
            return test_text

    return shortened + "..."


for index, headline in enumerate(
    headlines,
    start=1
):

    number = f"{index}."

    # Number की जगह
    draw.text(
        (45, start_y),
        number,
        fill="black",
        font=font_headline
    )

    # Headline
    safe_headline = fit_text(
        headline,
        font_headline,
        max_width - 75
    )

    draw.text(
        (85, start_y),
        safe_headline,
        fill="black",
        font=font_headline
    )

    start_y += line_height


# =========================
# SAVE
# =========================

image.save(
    "news_image.jpg",
    quality=95
)

print(
    f"News image created with "
    f"{len(headlines)} headlines."
)
