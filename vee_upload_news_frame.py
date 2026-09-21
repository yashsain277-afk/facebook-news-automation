import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import vee_upload_news as base

W, H = base.W, base.H
IST = base.IST
WORK = base.WORK

def make_frame_overlays(headline, body):
    os.makedirs(WORK, exist_ok=True)
    body = body or "यह खबर अभी चर्चा में है। प्रमुख अपडेट सामने आया है।"
    photo_box = (28, 305, 1052, 905)

    for idx in range(3):
        o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(o, "RGBA")

        # Permanent Vee News broadcast frame inspired by the approved reference.
        d.rectangle([0, 0, W, 305], fill=(4, 22, 65, 255))
        d.rectangle([0, 0, 22, H], fill=(220, 25, 32, 255))
        d.rectangle([1058, 0, W, H], fill=(220, 25, 32, 255))
        d.polygon([(280, 35), (1040, 35), (1010, 210), (280, 210)],
                  fill=(205, 18, 22, 255), outline=(255, 210, 70, 255), width=5)
        d.text((330, 55), "ब्रेकिंग न्यूज़",
               font=ImageFont.truetype(base.HINDI_BOLD, 82),
               fill="white", stroke_width=2, stroke_fill=(35, 35, 35, 255))
        d.text((465, 210), "बड़ी खबर",
               font=ImageFont.truetype(base.HINDI_BOLD, 52), fill="white")

        # Vee News shield-style logo block.
        d.rounded_rectangle([25, 35, 235, 250], 32,
                            fill=(8, 70, 150, 255),
                            outline=(255, 205, 50, 255), width=9)
        d.text((73, 62), "वी",
               font=ImageFont.truetype(base.HINDI_BOLD, 68),
               fill=(255, 205, 40, 255))
        d.text((54, 135), "न्यूज़",
               font=ImageFont.truetype(base.HINDI_BOLD, 45), fill="white")
        d.text((52, 260), "सच, सिर्फ सच",
               font=ImageFont.truetype(base.HINDI_BOLD, 25), fill="white")

        # Central uploaded photo/video area.
        d.rectangle(photo_box, outline="white", width=8)
        d.rectangle([28, 905, 1052, 916], fill=(255, 205, 40, 255))

        # Main dynamic headline panel.
        d.rectangle([28, 920, 1052, 1175],
                    fill=(5, 27, 75, 250),
                    outline=(225, 25, 32, 255), width=6)
        if idx == 0:
            title, text = "बड़ी खबर", headline[:180]
        elif idx == 1:
            title, text = "मुख्य अपडेट", body[:360]
        else:
            title, text = "वी न्यूज़ अपडेट", "ताज़ा खबरों के लिए VEE NEWS को FOLLOW करें"

        d.text((55, 935), title,
               font=ImageFont.truetype(base.HINDI_BOLD, 43),
               fill=(255, 210, 0))
        y = 990
        for line in base.wrap_mixed(d, text, 47, 940, True, 3):
            base.draw_mixed(d, (55, y), line, 47, "white", True)
            y += 61

        # Two dynamic information cards.
        d.rounded_rectangle([28, 1190, 635, 1570], 18,
                            fill=(245, 247, 250, 255), outline="white", width=5)
        d.rounded_rectangle([650, 1190, 1052, 1570], 18,
                            fill=(6, 30, 82, 255),
                            outline=(100, 180, 255, 255), width=5)

        if idx == 0:
            left_title, left_text = "खबर का सार", body[:420]
            points = ["मुख्य जानकारी", "ताज़ा अपडेट", "आगे की जानकारी पर अपडेट"]
        elif idx == 1:
            left_title, left_text = "विस्तृत जानकारी", (body + " " + headline)[:430]
            points = ["घटना से जुड़े तथ्य", "मुख्य पक्षों की जानकारी", "अगले अपडेट पर नज़र रखें"]
        else:
            left_title, left_text = "ताज़ा अपडेट", body[:430]
            points = ["वी न्यूज़ अपडेट", "निष्पक्ष और तेज़ खबरें", "नए अपडेट के लिए जुड़े रहें"]

        d.text((52, 1210), left_title,
               font=ImageFont.truetype(base.HINDI_BOLD, 38),
               fill=(10, 35, 90, 255))
        ly = 1265
        for line in base.wrap_mixed(d, left_text, 31, 545, False, 7):
            base.draw_mixed(d, (52, ly), line, 31, (15, 15, 20, 255), False)
            ly += 43

        d.text((675, 1210), "मुख्य बिंदु",
               font=ImageFont.truetype(base.HINDI_BOLD, 37),
               fill=(255, 210, 0))
        py = 1270
        for point in points:
            d.ellipse([675, py + 9, 690, py + 24], fill=(255, 210, 0, 255))
            for line in base.wrap_mixed(d, point, 29, 330, True, 2):
                base.draw_mixed(d, (705, py), line, 29, "white", True)
                py += 40
            py += 10

        # Permanent ticker/footer.
        d.rectangle([0, 1588, W, H], fill=(4, 20, 58, 255))
        d.rectangle([0, 1588, W, 1595], fill=(255, 205, 40, 255))
        d.text((35, 1610), "वी न्यूज़:",
               font=ImageFont.truetype(base.HINDI_BOLD, 39),
               fill=(255, 210, 0))
        d.text((225, 1615),
               "भारतीय खबरों की हर बड़ी अपडेट | निष्पक्ष, तेज़ और सटीक खबरें | VEE NEWS",
               font=ImageFont.truetype(base.HINDI_BOLD, 28), fill="white")
        d.rectangle([800, 1710, 1038, 1790],
                    fill=(205, 20, 25, 255),
                    outline=(255, 210, 70, 255), width=3)
        d.text((820, 1725), datetime.now(IST).strftime("%H:%M:%S"),
               font=ImageFont.truetype(base.ENG_BOLD, 38), fill="white")
        d.text((35, 1810),
               "ताज़ा खबरों के लिए VEE NEWS को FOLLOW करें",
               font=ImageFont.truetype(base.HINDI_BOLD, 34), fill="white")

        o.save(os.path.join(WORK, f"overlay{idx}.png"))

base.make_overlays = make_frame_overlays
base.main()
