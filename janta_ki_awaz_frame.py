import os
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

W, H = 990, 1280
IST = timezone(timedelta(hours=5, minutes=30))

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Bold.ttf" if bold else "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(draw, text, fnt, max_width):
    words = str(text or "").split()
    lines, line = [], ""
    for word in words:
        test = word if not line else line + " " + word
        if draw.textbbox((0,0), test, font=fnt)[2] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def make_frame(headline, source="", photo_path=None, output="janta_ki_awaz.jpg"):
    base = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(base)

    # Recreate the supplied 990x1280 जनता की आवाज़ reference frame.
    blue = (57, 58, 151)
    dark = (54, 52, 53)

    d.text((35, 25), "जनता की आवाज़", font=font(105, True), fill=blue)
    d.rectangle([0, 190, W, 250], fill=dark)
    d.text((120, 198), "बारां, अंता, मांगरोल, अटरू, छबड़ा, छीपाबड़ौद",
           font=font(35, True), fill="white")

    # News content area.
    if photo_path and os.path.exists(photo_path):
        try:
            photo = Image.open(photo_path).convert("RGB")
            photo.thumbnail((850, 470))
            x = (W - photo.width) // 2
            y = 285
            base.paste(photo, (x, y))
            d.rectangle([x-3, y-3, x+photo.width+3, y+photo.height+3], outline=blue, width=6)
            headline_y = max(790, y + photo.height + 25)
        except Exception:
            headline_y = 310
    else:
        headline_y = 320

    f_head = font(48, True)
    f_body = font(34, True)
    lines = wrap(d, headline, f_head, 900)[:5]
    total_h = len(lines) * 62
    y = headline_y
    if y + total_h > 1030:
        y = 760
    for line in lines:
        bbox = d.textbbox((0,0), line, font=f_head)
        x = (W - (bbox[2]-bbox[0])) // 2
        d.text((x, y), line, font=f_head, fill=blue)
        y += 62

    if source:
        src = f"स्रोत: {source}"
        bbox = d.textbbox((0,0), src, font=f_body)
        d.text(((W-(bbox[2]-bbox[0]))//2, min(y+20, 1060)), src, font=f_body, fill=dark)

    # Footer keeps the reference's clean white layout.
    d.rectangle([0, 1125, W, 1280], fill=blue)
    f_footer = font(31, True)
    now = datetime.now(IST).strftime("%d-%m-%Y %H:%M")
    d.text((35, 1145), "जनता की आवाज़", font=font(39, True), fill="white")
    d.text((35, 1195), "अंता | बारां | राजस्थान", font=f_footer, fill="white")
    d.text((690, 1195), now, font=font(25, True), fill="white")

    base.save(output, quality=94)
    return output
