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
        items.append((dt,category,title,summary,source,link))

items.sort(key=lambda x:x[0],reverse=True)
if not items:
    raise SystemExit("No new Indian political story found. Try the workflow again later.")
_,category,title,summary,source,link=items[0]

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

# Find a relevant Wikimedia Commons image of the named politician or party.
people = [
    ("Narendra Modi", ["modi", "narendra modi", "प्रधानमंत्री"]),
    ("Rahul Gandhi", ["rahul gandhi", "राहुल गांधी"]),
    ("Amit Shah", ["amit shah", "अमित शाह"]),
    ("Sonia Gandhi", ["sonia gandhi", "सोनिया गांधी"]),
    ("Mallikarjun Kharge", ["mallikarjun kharge", "खड़गे"]),
    ("Arvind Kejriwal", ["arvind kejriwal", "केजरीवाल"]),
    ("Mamata Banerjee", ["mamata banerjee", "ममता बनर्जी"]),
    ("Yogi Adityanath", ["yogi adityanath", "योगी आदित्यनाथ"]),
    ("Nirmala Sitharaman", ["nirmala sitharaman", "निर्मला सीतारमण"]),
    ("Rajnath Singh", ["rajnath singh", "राजनाथ सिंह"]),
    ("Akhilesh Yadav", ["akhilesh yadav", "अखिलेश यादव"]),
    ("Nitish Kumar", ["nitish kumar", "नीतीश कुमार"]),
    ("S Jaishankar", ["s jaishankar", "jaishankar", "जयशंकर"]),
]
low = title.lower()
person = next((name for name, terms in people if any(term in low for term in terms)), None)

def commons_image(search_term):
    try:
        params = {
            "action":"query","generator":"search","gsrsearch":search_term,
            "gsrnamespace":6,"gsrlimit":10,"prop":"imageinfo",
            "iiprop":"url","iiurlwidth":1200,"format":"json"
        }
        data=requests.get("https://commons.wikimedia.org/w/api.php",params=params,timeout=20).json()
        for p in data.get("query",{}).get("pages",{}).values():
            info=(p.get("imageinfo") or [{}])[0]
            u=info.get("thumburl") or info.get("url")
            if u and u.lower().split("?")[0].endswith((".jpg",".jpeg",".png",".webp")):
                return u
    except Exception as ex:
        print("Wikimedia search failed:", ex)
    return None

img_url = commons_image(person) if person else commons_image(title[:120])

W,H=1200,800
if img_url:
    try:
        raw=requests.get(img_url,timeout=30).content
        open("siyast_source.jpg","wb").write(raw)
        im=Image.open("siyast_source.jpg").convert("RGB")
        im.thumbnail((W,H))
        canvas=Image.new("RGB",(W,H),(20,24,35))
        x=(W-im.width)//2; y=(H-im.height)//2
        canvas.paste(im,(x,y))
        im=canvas
    except Exception:
        im=Image.new("RGB",(W,H),(20,24,35))
else:
    im=Image.new("RGB",(W,H),(20,24,35))

d=ImageDraw.Draw(im)
font="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
reg="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
fb=ImageFont.truetype(font,52)
fr=ImageFont.truetype(reg,30)
d.rectangle((0,0,W,105),fill=(12,16,25))
d.text((45,22),"सियासत",font=fb,fill=(245,245,245))
d.rectangle((0,665,W,800),fill=(12,16,25))
label = "ताज़ा भारतीय राजनीतिक अपडेट"
d.text((45,685),label,font=fr,fill=(245,245,245))
if person:
    d.text((45,735),person,font=fr,fill=(220,225,235))
else:
    d.text((45,735),"तथ्य • इतिहास • संदर्भ",font=fr,fill=(220,225,235))
with open("siyast_post.jpg","rb") as f:
    r=requests.post(f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos",
        data={"caption":caption,"access_token":TOKEN},
        files={"source":("siyast_post.jpg",f,"image/jpeg")},timeout=90)
print("Facebook:",r.status_code,r.text)
r.raise_for_status()

posted.append(title)
json.dump(posted[-300:],open(POSTED_FILE,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
