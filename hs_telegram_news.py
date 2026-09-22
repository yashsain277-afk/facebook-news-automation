import os, re, unicodedata, urllib.request, urllib.error, uuid
from PIL import Image, ImageDraw, ImageFont

PAGE_ID = os.environ["HS_NEWS_PAGE_ID"]
TOKEN = os.environ["HS_NEWS_PAGE_ACCESS_TOKEN"]
NEWS_TEXT = os.environ.get("HS_TELEGRAM_TEXT", "").strip()
OUTPUT = "hs_telegram_news.jpg"
W,H = 1200,900

HINDI="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
ENG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ENG_BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

NAVY=(5,35,58); RED=(220,20,30); YELLOW=(255,235,0); WHITE=(255,255,255)
BLUE=(10,55,125); BLACK=(20,28,40); LIGHT=(242,246,250); GREY=(105,120,135)

def font(path,size): return ImageFont.truetype(path,size)
def is_hi(c): return 0x0900 <= ord(c) <= 0x097F
def clean(t):
    t=unicodedata.normalize("NFC",str(t))
    return re.sub(r"\\s+"," ","".join(c if (is_hi(c) or c.isascii() or c.isdigit() or c in " .,।!?;:-–—()/₹'%+&@#*") else " " for c in t)).strip()
def draw_mixed(d,xy,text,size,fill,bold=False):
    x,y=xy; text=clean(text); hf=font(HINDI_BOLD if bold else HINDI,size); ef=font(ENG_BOLD if bold else ENG,size)
    cur=None; seg=""; cx=x
    for ch in text:
        typ="h" if is_hi(ch) else "e"
        if cur and typ!=cur:
            f=hf if cur=="h" else ef; d.text((cx,y),seg,font=f,fill=fill); cx=d.textbbox((cx,y),seg,font=f)[2]; seg=""
        seg+=ch; cur=typ
    if seg: d.text((cx,y),seg,font=hf if cur=="h" else ef,fill=fill)
def width(d,text,size,bold=False):
    text=clean(text); hf=font(HINDI_BOLD if bold else HINDI,size); ef=font(ENG_BOLD if bold else ENG,size)
    return sum(d.textbbox((0,0),c,font=hf if is_hi(c) else ef)[2] for c in text)
def wrap(text,size,maxw,bold=True):
    words=clean(text).split(); lines=[]; line=""
    for w in words:
        cand=w if not line else line+" "+w
        if width(draw,cand,size,bold)<=maxw: line=cand
        else:
            if line: lines.append(line)
            line=w
    if line: lines.append(line)
    return lines[:4]

if not NEWS_TEXT:
    raise RuntimeError("HS_TELEGRAM_TEXT is empty")

im=Image.new("RGB",(W,H),WHITE); draw=ImageDraw.Draw(im)

# Header matching the approved HS News Times frame.
draw.rectangle([0,0,W,250],fill=NAVY)
draw.rounded_rectangle([60,25,265,232],radius=25,fill=WHITE)
draw.ellipse([78,48,247,218],outline=(110,115,120),width=7)
draw.arc([88,58,237,207],start=210,end=25,fill=(24,155,215),width=12)
draw.rounded_rectangle([112,92,202,172],radius=8,outline=(30,155,205),width=5)
draw_mixed(draw,(128,103),"HS",43,(35,35,35),True)
draw_mixed(draw,(390,35),"HS",115,YELLOW,True)
draw.line([(655,42),(655,190)],fill=WHITE,width=3)
draw_mixed(draw,(695,38),"News",62,WHITE)
draw_mixed(draw,(695,105),"Times",62,WHITE)
draw.rectangle([0,250,W,266],fill=RED)

# Main card.
draw.rectangle([25,270,1175,820],fill=WHITE,outline=BLUE,width=4)
draw.polygon([(185,288),(215,288),(190,365),(160,365)],fill=BLUE)
draw.polygon([(985,288),(1015,288),(1040,365),(1010,365)],fill=BLUE)
draw.rounded_rectangle([245,278,955,370],radius=16,fill=RED)
draw_mixed(draw,(405,292),"ताज़ा बड़ी खबर",54,WHITE,True)

# Highlight headline.
draw.rounded_rectangle([55,395,1145,575],radius=16,fill=NAVY,outline=RED,width=4)
draw_mixed(draw,(90,415),"HS NEWS TIMES",28,YELLOW,True)
headline=NEWS_TEXT.splitlines()[0][:180]
lines=wrap(headline,36,990,True)
y=458
for line in lines:
    draw_mixed(draw,(90,y),line,36,WHITE,True); y+=48

# Details/source.
draw.rounded_rectangle([55,600,1145,770],radius=14,fill=LIGHT,outline=(210,220,230),width=3)
detail=" ".join(NEWS_TEXT.split())
if len(detail)>430: detail=detail[:430].rsplit(" ",1)[0]+"..."
lines=wrap(detail,25,1000,False)
y=620
for line in lines:
    draw_mixed(draw,(80,y),line,25,BLACK,False); y+=34

draw_mixed(draw,(80,748),"स्रोत: Telegram",22,BLUE,True)

# Footer.
draw.polygon([(0,805),(310,805),(360,900),(0,900)],fill=RED)
draw_mixed(draw,(28,820),"HS",55,WHITE,True)
draw_mixed(draw,(105,822),"News",30,WHITE,True)
draw_mixed(draw,(105,855),"Times",24,WHITE,True)
draw_mixed(draw,(410,822),"#HSNewsTimes",22,YELLOW,True)
draw_mixed(draw,(640,822),"#HindiNews",22,YELLOW,True)
draw_mixed(draw,(850,822),"#LocalNews",22,YELLOW,True)

im.save(OUTPUT,quality=95,optimize=True)

caption=f"📰 HS News Times | ताज़ा खबर\\n\\n{NEWS_TEXT}\\n\\nस्रोत: Telegram\\n\\n#HSNewsTimes #HindiNews #LocalNews"

boundary=uuid.uuid4().hex
with open(OUTPUT,"rb") as f: image_data=f.read()
body=(f"--{boundary}\\r\\nContent-Disposition: form-data; name=\"caption\"\\r\\n\\r\\n{caption}\\r\\n"
      f"--{boundary}\\r\\nContent-Disposition: form-data; name=\"access_token\"\\r\\n\\r\\n{TOKEN}\\r\\n"
      f"--{boundary}\\r\\nContent-Disposition: form-data; name=\"source\"; filename=\"hs_telegram_news.jpg\"\\r\\nContent-Type: image/jpeg\\r\\n\\r\\n").encode("utf-8")+image_data+f"\\r\\n--{boundary}--\\r\\n".encode("utf-8")
req=urllib.request.Request(f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos",data=body,headers={"Content-Type":f"multipart/form-data; boundary={boundary}"},method="POST")
try:
    with urllib.request.urlopen(req,timeout=60) as r: print("HS FACEBOOK POST:",r.read().decode())
except urllib.error.HTTPError as e:
    print("HS FACEBOOK ERROR:",e.read().decode("utf-8","replace")); raise
