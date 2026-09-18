from PIL import Image, ImageDraw, ImageFont
import json, sys, math

story = json.loads(sys.argv[1])
W, H = 1200, 900
img = Image.new("RGB", (W, H), (250, 235, 215))
d = ImageDraw.Draw(img)

# Decorative devotional background
for r in range(330, 40, -18):
    shade = (255, max(180, 225-r//4), max(140, 190-r//5))
    d.ellipse((600-r, 350-r, 600+r, 350+r), outline=shade, width=8)

# Halo and stylized goddess figure
d.ellipse((410, 90, 790, 470), outline=(218, 165, 70), width=18)
d.ellipse((470, 145, 730, 405), outline=(235, 190, 100), width=8)
d.ellipse((540, 185, 660, 305), fill=(245, 205, 165), outline=(150, 90, 55), width=5)
d.polygon([(500,180),(600,110),(700,180),(670,155),(530,155)], fill=(170,40,45))
d.polygon([(600,305),(500,420),(700,420)], fill=(175,45,65))
d.polygon([(500,420),(410,560),(790,560),(700,420)], fill=(190,55,75))
# lotus
for cx in range(420, 801, 70):
    d.ellipse((cx-55, 530, cx+55, 650), fill=(245, 145, 175), outline=(180,70,100), width=3)
d.ellipse((470, 555, 730, 665), fill=(250, 170, 190), outline=(180,70,100), width=4)

# trident and lamp symbols
d.line((865, 190, 865, 555), fill=(130,80,35), width=10)
d.line((830, 210, 865, 160), fill=(130,80,35), width=9)
d.line((900, 210, 865, 160), fill=(130,80,35), width=9)
d.arc((835,130,895,220), 180, 360, fill=(130,80,35), width=9)
d.ellipse((850,540,880,570), fill=(240,160,50))

HINDI = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
REG = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
hf = ImageFont.truetype(HINDI, 48)
rf = ImageFont.truetype(REG, 31)
small = ImageFont.truetype(REG, 25)

title = story["title"]
bbox = d.textbbox((0,0), title, font=hf)
d.text(((W-(bbox[2]-bbox[0]))/2, 680), title, font=hf, fill=(105,35,45))

devi = f"॥ {story['devi']} ॥"
bbox = d.textbbox((0,0), devi, font=rf)
d.text(((W-(bbox[2]-bbox[0]))/2, 755), devi, font=rf, fill=(125,75,35))

tag = "आदि शक्ति • श्रद्धा • भक्ति • सकारात्मक संदेश"
bbox = d.textbbox((0,0), tag, font=small)
d.text(((W-(bbox[2]-bbox[0]))/2, 825), tag, font=small, fill=(120,70,45))

img.save("adi_shakti_image.jpg", quality=95)
print("Created adi_shakti_image.jpg")
