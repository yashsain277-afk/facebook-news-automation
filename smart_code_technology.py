import feedparser, json, os, re, html, urllib.request, urllib.error, uuid
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

PAGE_ID=os.environ["FB_PAGE_ID"]; TOKEN=os.environ["FB_PAGE_ACCESS_TOKEN"]
POSTED_FILE="smart_code_posted.json"
FEEDS=[
("AI","https://news.google.com/rss/search?q=AI+artificial+intelligence+technology&hl=en&gl=IN&ceid=IN:en"),
("Computers","https://news.google.com/rss/search?q=computer+processor+GPU+technology&hl=en&gl=IN&ceid=IN:en"),
("Mobile","https://news.google.com/rss/search?q=smartphone+Android+iPhone+mobile+technology&hl=en&gl=IN&ceid=IN:en"),
("Software","https://news.google.com/rss/search?q=software+operating+system+developer+technology&hl=en&gl=IN&ceid=IN:en"),
("Cybersecurity","https://news.google.com/rss/search?q=cybersecurity+technology&hl=en&gl=IN&ceid=IN:en"),
]
try: posted=json.load(open(POSTED_FILE,encoding="utf-8"))
except: posted=[]
items=[]
for category,url in FEEDS:
    feed=feedparser.parse(url)
    for e in feed.entries[:12]:
        title=html.unescape(re.sub(r"\s+"," ",e.get("title","")).strip())
        if not title or title in posted: continue
        dt=None
        if e.get("published_parsed"): dt=datetime(*e.published_parsed[:6],tzinfo=timezone.utc)
        items.append((dt or datetime.min.replace(tzinfo=timezone.utc),category,title,e.get("link",""),e.get("source",{}).get("title","")))
items.sort(key=lambda x:x[0],reverse=True)
if not items: raise SystemExit("No new technology story found.")
_,category,title,link,source=items[0]
print("Selected:",title,"|",category,"|",source)

# Build a concise Hindi post from the verified headline; no invented technical claims.
caption=(f"💻 Smart Code Technology\n\n"
         f"🚀 आज की टेक्नोलॉजी अपडेट\n\n"
         f"📌 {title}\n\n"
         f"यह खबर {category} से जुड़ी नई तकनीकी जानकारी है। पूरी जानकारी और आधिकारिक विवरण के लिए मूल स्रोत देखें।\n\n"
         f"🔗 स्रोत: {source or 'Technology News'}\n"
         f"{link}\n\n"
         f"#SmartCodeTechnology #Technology #AI #Mobile #Software")

# Simple generated technology graphic
from PIL import Image,ImageDraw,ImageFont
W,H=1200,800
im=Image.new("RGB",(W,H),(18,24,38)); d=ImageDraw.Draw(im)
for x in range(0,W,80): d.line((x,0,x,H),fill=(45,55,75),width=1)
for y in range(0,H,80): d.line((0,y,W,y),fill=(45,55,75),width=1)
d.rounded_rectangle((70,70,1130,730),radius=28,outline=(90,110,150),width=4)
font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
reg="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
fb=ImageFont.truetype(font,58); fr=ImageFont.truetype(reg,34)
d.text((110,110),"SMART CODE TECHNOLOGY",font=fb,fill=(235,240,250))
d.text((110,190),category.upper(),font=fr,fill=(160,190,235))
# chip / circuit motif
d.rounded_rectangle((820,250,1030,460),radius=24,outline=(180,200,230),width=6)
d.rectangle((875,305,975,405),outline=(220,230,245),width=5)
for i in range(5):
    yy=285+i*42; d.line((770,yy,875,yy),fill=(130,170,220),width=4)
    d.line((975,yy,1080,yy),fill=(130,170,220),width=4)
d.text((110,300),"LATEST",font=fb,fill=(220,230,245))
d.text((110,380),"TECH UPDATE",font=fb,fill=(220,230,245))
# headline wrap
words=title.split(); lines=[]; line=""
for w in words:
    if len(line)+len(w)+1>42: lines.append(line); line=w
    else: line=(line+" "+w).strip()
if line: lines.append(line)
y=505
for ln in lines[:3]:
    d.text((110,y),ln,font=fr,fill=(220,225,235)); y+=48
im.save("smart_code_technology.jpg",quality=94)

import requests

with open("smart_code_technology.jpg", "rb") as image_file:
    response = requests.post(
        f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos",
        data={
            "caption": caption,
            "access_token": TOKEN,
        },
        files={
            "source": ("smart_code_technology.jpg", image_file, "image/jpeg")
        },
        timeout=60,
    )

print("Facebook status:", response.status_code)
print("Facebook response:", response.text)

response.raise_for_status()

posted.append(title)
with open(POSTED_FILE, "w", encoding="utf-8") as f:
    json.dump(posted[-200:], f, ensure_ascii=False, indent=2)
