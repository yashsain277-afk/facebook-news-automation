from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import re
import sys
import unicodedata

if len(sys.argv) < 2:
    raise ValueError("Headlines input नहीं मिला")

raw_input = sys.argv[1]

# Input format: headline || source
items = []
for line in raw_input.split("\n"):
    line = line.strip()
    if not line:
        continue
    if " || " in line:
        title, source = line.split(" || ", 1)
    else:
        title, source = line, ""
    items.append({"title": title.strip(), "source": source.strip()})
items = items[:10]

BACKGROUND = "veena news background.jpg"
OUTPUT = "news_image.jpg"
WIDTH, HEIGHT = 1200, 900

if not os.path.exists(BACKGROUND):
    raise FileNotFoundError(f"Background image not found: {BACKGROUND}")

background = Image.open(BACKGROUND).convert("RGB")
background = ImageOps.fit(background, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
canvas = Image.new("RGB", (WIDTH, HEIGHT), (245, 248, 252))
draw = ImageDraw.Draw(canvas)

HINDI = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
ENGLISH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ENGLISH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

for path, label in ((HINDI,"Hindi regular"),(HINDI_BOLD,"Hindi bold"),(ENGLISH,"English regular"),(ENGLISH_BOLD,"English bold")):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{label} font not found: {path}")

WHITE=(255,255,255); NAVY=(5,35,58); RED=(220,20,30); YELLOW=(255,235,0)
BLUE=(10,55,125); BLACK=(20,28,40); LIGHT=(242,246,250); GREY=(105,120,135)

def font(path,size):
    return ImageFont.truetype(path,size)

def is_hindi(c): return 0x0900 <= ord(c) <= 0x097F
def is_ascii_letter(c): return ("A"<=c<="Z") or ("a"<=c<="z")
def is_number(c): return "0"<=c<="9"
def is_allowed_punctuation(c): return c in " .,।!?;:-–—()/₹'%+&@#*"

def sanitize_text(text):
    text=unicodedata.normalize("NFC",str(text))
    return re.sub(r"\s+"," ","".join(c if (is_hindi(c) or is_ascii_letter(c) or is_number(c) or is_allowed_punctuation(c)) else " " for c in text)).strip()

def draw_mixed_text(xy,text,size,fill,bold=False):
    x,y=xy; text=sanitize_text(text)
    hf=font(HINDI_BOLD if bold else HINDI,size); ef=font(ENGLISH_BOLD if bold else ENGLISH,size)
    cur=None; seg=""; cx=x
    for ch in text:
        typ="hindi" if is_hindi(ch) else "english"
        if cur and typ!=cur:
            draw.text((cx,y),seg,font=hf if cur=="hindi" else ef,fill=fill)
            cx=draw.textbbox((cx,y),seg,font=hf if cur=="hindi" else ef)[2]; seg=""
        seg+=ch; cur=typ
    if seg: draw.text((cx,y),seg,font=hf if cur=="hindi" else ef,fill=fill)

def mixed_text_width(text,size,bold=False):
    text=sanitize_text(text); hf=font(HINDI_BOLD if bold else HINDI,size); ef=font(ENGLISH_BOLD if bold else ENGLISH,size)
    return sum(draw.textbbox((0,0),c,font=hf if is_hindi(c) else ef)[2] for c in text)

def shorten(text,size,max_width,bold=True):
    text=sanitize_text(text)
    if mixed_text_width(text,size,bold)<=max_width: return text
    out=""
    for word in text.split():
        cand=word if not out else out+" "+word
        if mixed_text_width(cand+"...",size,bold)<=max_width: out=cand
        else: break
    return (out+"...") if out else text[:12]+"..."

# --- Permanent HS News Times reference-frame layout ---
draw.rectangle([0,0,WIDTH,250],fill=NAVY)
# Decorative background beams.
draw.polygon([(0,0),(85,0),(0,95)],fill=BLUE)
draw.polygon([(1110,0),(1200,0),(1200,90)],fill=BLUE)
draw.polygon([(0,225),(80,150),(92,170),(25,250)],fill=YELLOW)
draw.polygon([(1200,205),(1140,250),(1115,230),(1180,185)],fill=YELLOW)

# HS logo block.
draw.rounded_rectangle([60,25,265,232],radius=25,fill=WHITE)
draw.ellipse([78,48,247,218],outline=(110,115,120),width=7)
draw.arc([88,58,237,207],start=210,end=25,fill=(24,155,215),width=12)
draw.rounded_rectangle([112,92,202,172],radius=8,outline=(30,155,205),width=5)
draw_mixed_text((128,103),"HS",43,(35,35,35),True)

draw_mixed_text((390,35),"HS",115,YELLOW,True)
draw.line([(655,42),(655,190)],fill=WHITE,width=3)
draw_mixed_text((695,38),"News",62,WHITE,False)
draw_mixed_text((695,105),"Times",62,WHITE,False)
draw.polygon([(1045,55),(1160,48),(1140,115),(1025,122)],fill=RED)
draw_mixed_text((1068,57),"हर खबर",30,WHITE,True)
draw.polygon([(1030,122),(1165,115),(1148,180),(1015,187)],fill=WHITE)
draw_mixed_text((1050,124),"आपके साथ",28,NAVY,True)
draw.rectangle([0,250,WIDTH,266],fill=RED)

# Main white card.
draw.rectangle([25,270,1175,875],fill=WHITE,outline=BLUE,width=4)
draw.polygon([(185,288),(215,288),(190,365),(160,365)],fill=BLUE)
draw.polygon([(985,288),(1015,288),(1040,365),(1010,365)],fill=BLUE)
draw.rounded_rectangle([245,278,955,370],radius=16,fill=RED)
draw_mixed_text((378,292),"आज की 10 बड़ी खबरें",54,WHITE,True)

# Left neutral news panel keeps the template reusable for all local-news topics.
draw.rounded_rectangle([45,390,385,790],radius=18,fill=NAVY,outline=BLUE,width=4)
draw_mixed_text((92,455),"HS",95,YELLOW,True)
draw_mixed_text((85,565),"NEWS",55,WHITE,True)
draw_mixed_text((78,630),"आज की खबरें",34,WHITE,True)
draw_mixed_text((65,690),"ताज़ा • स्थानीय • हिंदी",24,YELLOW,True)

headline_size=22; source_size=15; start_y=395; row_h=45
num_font=font(ENGLISH_BOLD,22)
for i in range(10):
    y=start_y+i*row_h
    draw.ellipse([425,y,468,y+43],fill=RED)
    nb=draw.textbbox((0,0),str(i+1),font=num_font); nw=nb[2]-nb[0]
    draw.text((446-nw/2,y+7),str(i+1),font=num_font,fill=WHITE)
    if i < len(items):
        title=shorten(items[i]["title"],headline_size,545,True)
        source=shorten(items[i]["source"],source_size,145,False) if items[i]["source"] else ""
        draw_mixed_text((480,y+3),title,headline_size,BLACK,True)
        if source:
            sw=mixed_text_width(source,source_size,False)
            draw_mixed_text((1110-sw,y+7),source,source_size,GREY,False)
    draw.line([(480,y+43),(1135,y+43)],fill=(215,222,230),width=1)

# Footer.
draw.polygon([(0,805),(260,805),(310,875),(0,875)],fill=RED)
draw_mixed_text((28,820),"HS",55,WHITE,True)
draw_mixed_text((105,822),"News",30,WHITE,True)
draw_mixed_text((105,855),"Times",24,WHITE,True)
draw_mixed_text((390,822),"#HSNewsTimes",22,YELLOW,True)
draw_mixed_text((610,822),"|",24,WHITE,True)
draw_mixed_text((650,822),"#HindiNews",22,YELLOW,True)
draw_mixed_text((830,822),"|",24,WHITE,True)
draw_mixed_text((870,822),"#LocalNews",22,YELLOW,True)
draw.polygon([(1040,805),(1200,805),(1200,875),(1010,875)],fill=RED)
draw_mixed_text((1050,818),"ताज़ा खबरें",24,WHITE,True)
draw_mixed_text((1050,850),"हर 2 घंटे",27,YELLOW,True)

canvas.save(OUTPUT, quality=95, optimize=True)
print(f"Final Veena News template image created: {OUTPUT}")
