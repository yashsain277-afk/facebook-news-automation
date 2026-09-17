from PIL import Image, ImageDraw, ImageFont
import sys

headlines_text = sys.argv[1]

headlines = [
    line.strip()
    for line in headlines_text.split("\n")
    if line.strip()
]

headlines = headlines[:10]

WIDTH = 1200
HEIGHT = 630

image = Image.new("RGB", (WIDTH, HEIGHT), "white")
draw = ImageDraw.Draw(image)

# Fonts
HINDI_FONT = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
ENGLISH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

font_brand = ImageFont.truetype(ENGLISH_BOLD, 28)
font_section = ImageFont.truetype(HINDI_BOLD, 25)
font_headline = ImageFont.truetype(HINDI_FONT, 22)

# Header
draw.rectangle([(0, 0), (WIDTH, 78)], fill="black")
draw.text((40, 22), "VEENA NEWS", fill="white", font=font_brand)

draw.text((40, 96), "आज की 10 बड़ी खबरें", fill="black", font=font_section)

# Headline area
start_y = 145
line_height = 46

def shorten_text(text, max_chars=85):
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."

for index, headline in enumerate(headlines, start=1):
    number = f"{index}."
    safe_headline = shorten_text(headline)

    draw.text(
        (40, start_y),
        number,
        fill="black",
        font=font_headline
    )

    draw.text(
        (82, start_y),
        safe_headline,
        fill="black",
        font=font_headline
    )

    start_y += line_height

# Footer
draw.line([(40, 602), (1160, 602)], fill="black", width=1)
draw.text(
    (40, 608),
    "Veena News",
    fill="black",
    font=ImageFont.truetype(ENGLISH_BOLD, 16)
)

image.save("news_image.jpg", quality=95)

print(f"News image created with {len(headlines)} headlines.")
