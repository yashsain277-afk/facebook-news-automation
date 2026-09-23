import os
import unicodedata
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 990, 1280
BLUE = (57, 58, 151)
DARK = (54, 52, 53)

FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"

def font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REG
    if not os.path.exists(path):
        raise RuntimeError(f"Hindi font missing: {path}")
    return ImageFont.truetype(path, size)

def clean_text(value):
    # Normalize Unicode so Hindi combining sequences render consistently.
    text = unicodedata.normalize("NFC", str(value or ""))
    # Never allow an already-corrupted replacement character into the graphic.
    return text.replace("\ufffd", "").strip()

def wrap(draw, text, fnt, max_width):
    words = clean_text(text).split()
    lines, line = [], ""
    for word in words:
        test = word if not line else line + " " + word
        if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def make_frame(headline, source="", photo_path=None, output="janta_ki_awaz.jpg"):
    # Match the user's supplied frame: 990x1280, white body, no added footer.
    base = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(base)

    d.text((35, 25), "जनता की आवाज़", font=font(105, True), fill=BLUE)
    d.rectangle([0, 190, W, 250], fill=DARK)
    area = "बारां, अंता, मांगरोल, अटरू, छबड़ा, छीपाबड़ौद"
    af = font(35, True)
    bbox = d.textbbox((0, 0), area, font=af)
    d.text(((W-(bbox[2]-bbox[0]))//2, 198), area, font=af, fill="white")

    content_top = 285
    content_bottom = H - 35

    if photo_path and os.path.exists(photo_path):
        photo = Image.open(photo_path).convert("RGB")
        photo.thumbnail((850, 500), Image.Resampling.LANCZOS)
        x = (W - photo.width) // 2
        y = content_top
        base.paste(photo, (x, y))
        d.rectangle([x-2, y-2, x+photo.width+2, y+photo.height+2], outline=BLUE, width=4)
        headline_y = y + photo.height + 28
    else:
        headline_y = content_top

    title = clean_text(headline)
    # Avoid overflow while preserving readable Hindi.
    f_head = font(47, True)
    lines = wrap(d, title, f_head, 900)[:6]

    y = headline_y
    if y + len(lines) * 64 > content_bottom - 70:
        f_head = font(39, True)
        lines = wrap(d, title, f_head, 900)[:7]

    for line in lines:
        bbox = d.textbbox((0, 0), line, font=f_head)
        x = (W - (bbox[2]-bbox[0])) // 2
        d.text((x, y), line, font=f_head, fill=BLUE)
        y += f_head.size + 12

    src = clean_text(source)
    if src:
        sf = font(27, True)
        src_text = "स्रोत: " + src
        bbox = d.textbbox((0, 0), src_text, font=sf)
        d.text(((W-(bbox[2]-bbox[0]))//2, min(y+18, content_bottom-42)),
               src_text, font=sf, fill=DARK)

    base.save(output, format="JPEG", quality=95, optimize=True)
    print("JANTA FRAME CREATED:", output)

if __name__ == "__main__":
    make_frame("टेस्ट न्यूज़ — जनता की आवाज़", "amarujala.com")
