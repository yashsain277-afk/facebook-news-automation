import feedparser, json, os, re, html, requests, textwrap
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote
import subprocess

PAGE_ID=os.environ["FB_PAGE_ID"]; TOKEN=os.environ["FB_PAGE_ACCESS_TOKEN"]
POSTED_FILE="siyast_posted.json"

FEEDS=[
("राष्ट्रीय राजनीति","https://news.google.com/rss/search?q=India+politics+Parliament+government+political+parties&hl=hi&gl=IN&ceid=IN:hi"),
("प्रधानमंत्री और केंद्र","https://news.google.com/rss/search?q=India+Prime+Minister+central+government+politics+India&hl=hi&gl=IN&ceid=IN:hi"),
("विपक्ष और संसद","https://news.google.com/rss/search?q=India+opposition+Parliament+politics+India&hl=hi&gl=IN&ceid=IN:hi"),
("राज्य राजनीति","https://news.google.com/rss/search?q=India+Indian+state+politics+Chief+Minister+politics&hl=hi&gl=IN&ceid=IN:hi"),
]

try: posted=json.load(open(POSTED_FILE,encoding="utf-8"))
except: posted=[]

items=[]
for category,url in FEEDS:
    feed=feedparser.parse(url)
    for e in feed.entries[:15]:
        title=html.unescape(re.sub(r"\s+"," ",e.get("title","")).strip())
        if not title or title in posted: continue
        dt=datetime.min.replace(tzinfo=timezone.utc)
        if e.get("published_parsed"): dt=datetime(*e.published_parsed[:6],tzinfo=timezone.utc)
        summary=html.unescape(re.sub(r"<[^>]+>"," ",e.get("summary","")))
        summary=re.sub(r"\s+"," ",summary).strip()
        source=e.get("source",{}).get("title","") or "News source"
        link=e.get("link","")
        media_url = None
        media = e.get("media_content") or e.get("media_thumbnail") or []
        if media and isinstance(media, list):
            media_url = media[0].get("url")
        items.append((dt,category,title,summary,source,link,media_url))

items.sort(key=lambda x:x[0],reverse=True)
if not items:
    raise SystemExit("No new Indian political story found. Try the workflow again later.")
_,category,title,summary,source,link,news_image_url=items[0]

# Keep the post factual and neutral. The text is built from the news item's supplied summary.
summary=summary[:1600]
base=(f"यह खबर भारतीय राजनीति से जुड़े एक ताज़ा घटनाक्रम पर आधारित है। "
      f"उपलब्ध समाचार विवरण के अनुसार, {title}। ")
if summary:
    base+=f"समाचार में उपलब्ध विवरण के अनुसार, {summary} "
base+=("इस घटनाक्रम को समझते समय संबंधित नेता, राजनीतिक दल और संस्थाओं के आधिकारिक बयान "
       "तथा मूल समाचार रिपोर्ट को प्राथमिक संदर्भ माना जाना चाहिए। "
       "भारतीय लोकतंत्र में अलग-अलग दलों और नेताओं के फैसलों का प्रभाव नीति, प्रशासन, "
       "संसद, राज्यों और आम नागरिकों पर अलग-अलग रूप में पड़ सकता है। "
       "इसलिए इस पोस्ट का उद्देश्य किसी दल या नेता के पक्ष या विपक्ष में राय बनाना नहीं, "
       "बल्कि उपलब्ध स्रोत के आधार पर घटनाक्रम और उसका संदर्भ सामने रखना है।")
words=base.split()
if len(words)<200:
    base += ("\n\nऐतिहासिक संदर्भ के लिए भारतीय राजनीति में संविधान, संसद, चुनाव, "
             "संघवाद और राजनीतिक दलों की भूमिका को समझना उपयोगी है। समय के साथ सरकारों "
             "और विपक्ष ने अलग-अलग परिस्थितियों में महत्वपूर्ण निर्णय लिए हैं। किसी निर्णय "
             "का मूल्यांकन करते समय उसके समय की परिस्थितियों, उपलब्ध विकल्पों और बाद में "
             "दिखाई देने वाले परिणामों को अलग-अलग देखना आवश्यक है।")
words=base.split()
text=" ".join(words[:390])
if len(text.split())<200:
    text+=" यह विषय आगे भी सार्वजनिक बहस और लोकतांत्रिक संस्थाओं के निर्णयों के संदर्भ में महत्वपूर्ण बना रह सकता है।"

caption=(f"📰 सियासत | {title}\n\n{text}\n\n"
         f"📚 संदर्भ / Reference: {source}\n"
         f"🔗 मूल समाचार: {link}\n\n"
         f"#Siyasat #IndianPolitics #Bharat #IndianDemocracy #PoliticalNews")



# Use the single saved Siyasat template image on every post.
# No leader photos are downloaded and no new base image is generated.
TEMPLATE_FILE = "siyast_template.jpg"

W, H = 1200, 800
im = Image.open(TEMPLATE_FILE).convert("RGB")

# Replace only the headline area of the saved template.
# The permanent faces, Parliament, party symbols, branding and overall design remain unchanged.
d = ImageDraw.Draw(im)

def find_hindi_font(style):
    candidates = [
        f"Noto Sans Devanagari:style={style}",
        "Noto Sans Devanagari"
    ]
    for pattern in candidates:
        try:
            path = subprocess.check_output(
                ["fc-match", "-f", "%{file}", pattern],
                text=True
            ).strip()
            if path and os.path.isfile(path):
                return path
        except Exception:
            pass

    fallback = {
        "Bold": "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "Regular": "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
    }
    if os.path.isfile(fallback[style]):
        return fallback[style]
    raise RuntimeError("Noto Sans Devanagari font is not installed")

font_bold = find_hindi_font("Bold")
font_reg = find_hindi_font("Regular")

def fit_font(path, size):
    return ImageFont.truetype(path, size)

f_head = fit_font(font_bold, 38)
f_sub = fit_font(font_bold, 27)

# Right-side headline block in the saved 1200x800 template.
# Cover the old baked-in headline, then redraw the new headline in the same style.
d.rectangle((690, 382, 1190, 585), fill=(248, 248, 245))
d.rectangle((690, 475, 1190, 558), fill=(215, 30, 30))
d.rectangle((690, 558, 1190, 620), fill=(242, 195, 0))

headline = re.sub(r"\s+", " ", title).strip()
headline_lines = textwrap.wrap(
    headline,
    width=24,
    break_long_words=False,
    break_on_hyphens=False
)[:4]

# First line(s) on white band.
y = 397
for line in headline_lines[:2]:
    d.text((710, y), line, font=f_head, fill=(10, 10, 10))
    y += 42

# If the title needs more lines, put the remaining short portion on the red band.
remaining = headline_lines[2:]
if remaining:
    y = 483
    for line in remaining[:2]:
        d.text((710, y), line, font=f_head, fill=(255, 255, 255))
        y += 42

d.text((715, 570), "सियासत • ताज़ा राजनीतिक अपडेट", font=f_sub, fill=(20, 20, 20))

im.save("siyast_post.jpg", quality=92, optimize=True)

with open("siyast_post.jpg", "rb") as f:
    r = requests.post(
        f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos",
        data={"caption": caption, "access_token": TOKEN},
        files={"source": ("siyast_post.jpg", f, "image/jpeg")},
        timeout=90
    )
print("Facebook:", r.status_code, r.text)
r.raise_for_status()

posted.append(title)
json.dump(
    posted[-300:],
    open(POSTED_FILE, "w", encoding="utf-8"),
    ensure_ascii=False,
    indent=2
)
