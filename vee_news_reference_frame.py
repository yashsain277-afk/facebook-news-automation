import os
from datetime import datetime
from PIL import Image, ImageDraw
import vee_news_automation as base

IST = base.IST
OUTPUT = base.OUTPUT
font = base.font
draw_mixed = base.draw_mixed
wrap_mixed = base.wrap_mixed
load_news_photo = base.load_news_photo
crop_cover = base.crop_cover
simple_title = base.simple_title
simple_summary = base.simple_summary

def create_image(item):
    # Permanent Vee News frame based on the user-approved 1024x1536 reference layout.
    W, H = 1024, 1536
    im = Image.new("RGB", (W, H), (4, 25, 72))
    d = ImageDraw.Draw(im)
    navy = (4, 25, 72); blue = (10, 57, 130); red = (226, 20, 27)
    yellow = (255, 214, 0); white = (255, 255, 255); dark = (12, 28, 55)
    light = (247, 249, 252)

    # Header/logo area.
    d.rectangle([0, 0, W, 285], fill=navy)
    d.polygon([(0, 0), (285, 0), (238, 285), (0, 285)], fill=(8, 66, 150))
    d.rounded_rectangle([30, 22, 245, 245], radius=26, fill=(8, 58, 130), outline=yellow, width=8)
    d.polygon([(48, 48), (137, 28), (226, 48), (215, 190), (137, 230), (57, 190)],
              fill=(10, 72, 150), outline=white, width=3)
    draw_mixed(d, (78, 54), "वी", 76, yellow, True)
    draw_mixed(d, (55, 137), "न्यूज़", 46, white, True)
    draw_mixed(d, (50, 258), "सच, सिर्फ सच", 26, white, True)

    d.polygon([(282, 48), (993, 48), (957, 205), (282, 205)],
              fill=red, outline=(255, 235, 170), width=4)
    draw_mixed(d, (348, 60), "ब्रेकिंग न्यूज़", 82, white, True)
    d.polygon([(278, 205), (927, 205), (914, 277), (264, 277)],
              fill=navy, outline=white, width=5)
    draw_mixed(d, (460, 210), "बड़ी खबर", 50, white, True)

    # Dynamic news photo area.
    photo_box = (27, 294, 997, 752)
    photo = load_news_photo(item)
    if photo:
        im.paste(crop_cover(photo, (970, 450)), (27, 299))
        d = ImageDraw.Draw(im)
    else:
        d.rectangle([27, 299, 996, 747], fill=blue)
        draw_mixed(d, (95, 425), "VEE NEWS", 80, white, True)
    d.rectangle(photo_box, outline=white, width=6)
    d.rounded_rectangle([684, 695, 995, 750], radius=7, fill=yellow)
    draw_mixed(d, (744, 705), "क्रिकेट अपडेट", 28, dark, True)

    # Dynamic headline panel.
    d.rectangle([27, 753, 997, 1012], fill=navy, outline=red, width=6)
    title_lines = wrap_mixed(d, simple_title(item), 48, 900, True, 3)
    y = 772
    for line in title_lines:
        draw_mixed(d, (52, y), line, 48, white, True)
        y += 57
    if len(title_lines) < 3:
        draw_mixed(d, (150, min(958, y + 5)), "मुख्य अपडेट", 40, yellow, True)

    # Lower information cards.
    d.rounded_rectangle([25, 1024, 606, 1402], radius=8, fill=light, outline=white, width=5)
    d.rounded_rectangle([617, 1024, 999, 1402], radius=8, fill=navy, outline=(120, 190, 255), width=5)
    draw_mixed(d, (50, 1042), "मुख्य जानकारी", 38, blue, True)
    lines = wrap_mixed(d, simple_summary(item), 30, 515, False, 7)
    y = 1100
    for line in lines:
        draw_mixed(d, (50, y), line, 30, dark, False)
        y += 45
    draw_mixed(d, (50, 1360), "आगे की जानकारी पर अपडेट किया जाएगा।", 24, blue, True)

    draw_mixed(d, (640, 1042), "मुख्य बिंदु", 38, yellow, True)
    points = ["क्रिकेट से जुड़ी ताज़ा खबर", "मुख्य अपडेट और जानकारी",
              "टीम इंडिया पर नजर", "आगे के अपडेट जल्द"]
    y = 1100
    for point in points:
        d.ellipse([640, y + 8, 655, y + 23], fill=yellow)
        for line in wrap_mixed(d, point, 27, 315, True, 2):
            draw_mixed(d, (670, y), line, 27, white, True)
            y += 37
        y += 12

    # Permanent ticker/footer.
    d.rectangle([0, 1408, W, H], fill=navy)
    d.rectangle([0, 1408, W, 1416], fill=yellow)
    draw_mixed(d, (45, 1430), "वी न्यूज़:", 36, yellow, True)
    draw_mixed(d, (190, 1434), "देश-दुनिया की हर बड़ी खबर, सबसे पहले", 28, white, True)
    draw_mixed(d, (45, 1480), "क्रिकेट | खेल | राजनीति | मनोरंजन | और भी बहुत कुछ...", 25, white, True)
    d.rectangle([820, 1450, 1000, 1515], fill=red, outline=yellow, width=3)
    d.text((838, 1462), datetime.now(IST).strftime("%H:%M:%S"),
           font=font(base.ENG_BOLD, 30), fill=white)
    d.rectangle([0, 1522, W, H], fill=(2, 17, 50))
    draw_mixed(d, (42, 1534), "ताज़ा खबरों के लिए VEE NEWS को FOLLOW करें", 25, white, True)

    im.save(OUTPUT, quality=94, optimize=True)

base.create_image = create_image

if __name__ == "__main__":
    base.main()
