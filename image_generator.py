from PIL import Image, ImageDraw, ImageFont
import sys


headline = sys.argv[1]

WIDTH = 1200
HEIGHT = 630

image = Image.new("RGB", (WIDTH, HEIGHT), "white")
draw = ImageDraw.Draw(image)


# Fonts
HINDI_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
HINDI_REGULAR = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"

ENGLISH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ENGLISH_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


font_title = ImageFont.truetype(
    HINDI_BOLD,
    48
)

font_brand = ImageFont.truetype(
    ENGLISH_BOLD,
    32
)

font_footer_hindi = ImageFont.truetype(
    HINDI_REGULAR,
    28
)

font_footer_english = ImageFont.truetype(
    ENGLISH_REGULAR,
    28
)


# Top header
draw.rectangle(
    [(0, 0), (WIDTH, 105)],
    fill="black"
)

draw.text(
    (55, 28),
    "VEENA NEWS",
    fill="white",
    font=font_brand
)


# Headline wrapping
max_width = 1080
words = headline.split()

lines = []
current_line = ""

for word in words:

    test_line = (
        current_line + " " + word
    ).strip()

    bbox = draw.textbbox(
        (0, 0),
        test_line,
        font=font_title
    )

    line_width = bbox[2] - bbox[0]

    if line_width <= max_width:
        current_line = test_line

    else:

        if current_line:
            lines.append(current_line)

        current_line = word


if current_line:
    lines.append(current_line)


# Maximum 5 lines
lines = lines[:5]


# Draw headline
y = 175

for line in lines:

    draw.text(
        (60, y),
        line,
        fill="black",
        font=font_title
    )

    y += 72


# Footer
draw.text(
    (60, 555),
    "ताज़ा खबर",
    fill="black",
    font=font_footer_hindi
)

draw.text(
    (220, 555),
    "• Veena News",
    fill="black",
    font=font_footer_english
)


# Save image
image.save(
    "news_image.jpg",
    quality=95
)

print("Hindi news image created successfully.")
