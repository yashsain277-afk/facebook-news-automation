from PIL import Image, ImageDraw, ImageFont
import textwrap
import sys


headline = sys.argv[1]

WIDTH = 1200
HEIGHT = 630

# Background
image = Image.new("RGB", (WIDTH, HEIGHT), "white")
draw = ImageDraw.Draw(image)

# Hindi fonts
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"

font_title = ImageFont.truetype(FONT_BOLD, 48)
font_brand = ImageFont.truetype(FONT_BOLD, 32)
font_footer = ImageFont.truetype(FONT_REGULAR, 28)

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

# Limit to 5 lines
lines = lines[:5]

# Headline
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
    "ताज़ा खबर • Veena News",
    fill="black",
    font=font_footer
)

# Save
image.save(
    "news_image.jpg",
    quality=95
)

print("Hindi news image created successfully.")
