import feedparser, json, os, re, html, requests, textwrap
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote

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


# Permanent 1200x800 visual template.
# The layout and leader portraits stay the same on every post; only the headline changes.
LEADERS = [
    ("नरेंद्र मोदी", "BJP", "https://commons.wikimedia.org/wiki/Special:Redirect/file/Official_portrait_of_prime_minister_of_India,_Narendra_Modi.jpg"),
    ("राहुल गांधी", "INC", "https://commons.wikimedia.org/wiki/Special:Redirect/file/Rahul_Gandhi.jpg"),
    ("अमित शाह", "BJP", "https://commons.wikimedia.org/wiki/Special:Redirect/file/Sh_Amit_Shah.jpg"),
    ("मल्लिकार्जुन खड़गे", "INC", "https://commons.wikimedia.org/wiki/Special:Redirect/file/Mallikarjun_Kharge.jpg"),
]

W, H = 1200, 800
BG = (12, 16, 27)
PANEL = (28, 34, 49)
WHITE = (248, 249, 252)
MUTED = (190, 197, 210)
ACCENT = (225, 173, 62)

font_bold = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
font_reg = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"

def fit_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(font_bold, size)

fb = fit_font(font_bold, 50)
fsub = fit_font(font_reg, 24)
fheadline = fit_font(font_bold, 42)
fname = fit_font(font_bold, 22)
fparty = fit_font(font_reg, 20)
fyear = fit_font(font_bold, 34)

def download_image(url, filename):
    try:
        rr = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "SiyasatNewsBot/1.0"},
            allow_redirects=True
        )
        rr.raise_for_status()
        with open(filename, "wb") as fh:
            fh.write(rr.content)
        return Image.open(filename).convert("RGB")
    except Exception as ex:
        print("Leader image download failed:", url, ex)
        return None

def cover_crop(src, size):
    tw, th = size
    src = src.copy()
    scale = max(tw / src.width, th / src.height)
    nw, nh = int(src.width * scale), int(src.height * scale)
    src = src.resize((nw, nh), Image.LANCZOS)
    left = max(0, (nw - tw) // 2)
    top = max(0, (nh - th) // 2)
    return src.crop((left, top, left + tw, top + th))

im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im)

# Header
d.rectangle((0, 0, W, 112), fill=(9, 13, 22))
d.text((38, 18), "सियासत", font=fb, fill=WHITE)
d.text((40, 73), "भारतीय राजनीति • समाचार • इतिहास • संदर्भ", font=fsub, fill=MUTED)
d.text((1060, 25), "2029", font=fyear, fill=WHITE)

# Headline panel
d.rounded_rectangle((30, 132, W - 30, 430), radius=24, fill=PANEL)
d.rectangle((30, 132, 48, 430), fill=ACCENT)

headline = re.sub(r"\s+", " ", title).strip()
headline_lines = textwrap.wrap(
    headline,
    width=43,
    break_long_words=False,
    break_on_hyphens=False
)[:5]

line_height = 55
total_h = len(headline_lines) * line_height
start_y = 280 - total_h // 2

for i, line in enumerate(headline_lines):
    d.text((72, start_y + i * line_height), line, font=fheadline, fill=WHITE)

# Fixed leader strip
card_y = 458
card_h = 300
gap = 18
card_w = (W - 60 - gap * 3) // 4

for i, (name, party, url) in enumerate(LEADERS):
    x = 30 + i * (card_w + gap)
    d.rounded_rectangle((x, card_y, x + card_w, card_y + card_h), radius=18, fill=(20, 25, 38))

    portrait = download_image(url, f"leader_{i}.jpg")
    if portrait:
        portrait = cover_crop(portrait, (card_w - 20, 205))
        im.paste(portrait, (x + 10, card_y + 10))
        d = ImageDraw.Draw(im)
    else:
        d.rectangle((x + 10, card_y + 10, x + card_w - 10, card_y + 215), fill=(45, 50, 65))
        d.text((x + 25, card_y + 90), name, font=fparty, fill=MUTED)

    d.text((x + 14, card_y + 225), name, font=fname, fill=WHITE)
    pill_w = 62
    d.rounded_rectangle((x + 14, card_y + 258, x + 14 + pill_w, card_y + 286), radius=10, fill=(235, 235, 235))
    d.text((x + 27, card_y + 261), party, font=fparty, fill=(20, 24, 32))

# Footer
d.text((930, 768), "तथ्य • इतिहास • संदर्भ", font=fparty, fill=MUTED)

im.save("siyast_post.jpg", quality=92)

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
json.dump(posted[-300:], open(POSTED_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
