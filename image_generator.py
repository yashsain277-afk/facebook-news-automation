from PIL import Image, ImageDraw, ImageFont
import textwrap
import sys


headline = sys.argv[1]

WIDTH = 1200
HEIGHT = 630

image = Image.new("RGB", (WIDTH, HEIGHT), "white")
draw = ImageDraw.Draw(image)

# Fonts
font_large = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    52
)

font_small = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    30
)

# Header
draw.rectangle(
    [(0, 0), (WIDTH, 100)],
    fill="black"
)

draw.text(
    (50, 30),
    "VEENA NEWS",
    fill="white",
    font=font_small
)

# Headline
lines = textwrap.wrap(headline, width=32)

y = 170

for line in lines:
    draw.text(
        (60, y),
        line,
        fill="black",
        font=font_large
    )
    y += 75

# Footer
draw.text(
    (60, 550),
    "ताज़ा खबर • Veena News",
    fill="black",
    font=font_small
)

image.save("news_image.jpg", quality=95)

print("Image created: news_image.jpg")
