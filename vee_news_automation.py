import os
import json
import re
import html
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher

import feedparser
from PIL import Image, ImageDraw, ImageFont

PAGE_ID = os.environ["VEE_NEWS_PAGE_ID"]
ACCESS_TOKEN = os.environ["VEE_NEWS_PAGE_ACCESS_TOKEN"]
STATE_FILE = "vee_news_state.json"
OUTPUT = "vee_news_image.jpg"
WIDTH, HEIGHT = 1080, 1920
PHONE = "8824814646"

CRICKET_FEEDS = {
    "Indian Cricket": "https://news.google.com/rss/search?q=Indian+cricket+OR+Team+India+OR+BCCI&hl=hi&gl=IN&ceid=IN:hi",
    "IPL": "https://news.google.com/rss/search?q=IPL+cricket+India&hl=hi&gl=IN&ceid=IN:hi",
    "India Players": "https://news.google.com/rss/search?q=Virat+Kohli+OR+Rohit+Sharma+OR+Shubman+Gill+OR+Jasprit+Bumrah&hl=hi&gl=IN&ceid=IN:hi",
    "Cricket": "https://news.google.com/rss/search?q=cricket+India&hl=hi&gl=IN&ceid=IN:hi",
}
GENERAL_FEEDS = {
    "Trending India": "https://news.google.com/rss/search?q=India+trending+news&hl=hi&gl=IN&ceid=IN:hi",
    "India": "https://news.google.com/rss/search?q=India+latest+news&hl=hi&gl=IN&ceid=IN:hi",
}
IST = timezone(timedelta(hours=5, minutes=30))

def clean_html(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(text or "")))
    return re.sub(r"\s+", " ", text).strip()

def normalize(text):
    text = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    return re.sub(r"\s+-\s+[^-]+$", "", text)

def source_of(entry):
    try:
        s = entry.source.get("title", "")
        if s: return str(s).strip()
    except Exception:
        pass
    title = str(entry.get("title", ""))
    return title.rsplit(" - ", 1)[1].strip() if " - " in title else "Google News"

def published_of(entry):
    try:
        if entry.get("published_parsed"):
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if entry.get("updated_parsed"):
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    except Exception:
        pass
    return datetime.now(timezone.utc)

def collect(feeds, kind):
    out = []
    for category, url in feeds.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:12]:
            title = clean_html(entry.get("title", ""))
            link = entry.get("link", "")
            if not title or not link: continue
            summary = clean_html(entry.get("summary", "") or entry.get("description", ""))
            out.append({"title":title,"link":link,"source":source_of(entry),
                        "summary":summary,"published":published_of(entry),
                        "kind":kind,"category":category})
    return out

def dedupe(items):
    result, links, titles = [], set(), []
    for item in sorted(items, key=lambda x:x["published"], reverse=True):
        if item["link"] in links: continue
        n = normalize(item["title"])
        if any(SequenceMatcher(None,n,old).ratio() >= 0.88 for old in titles): continue
        links.add(item["link"]); titles.append(n); result.append(item)
    return result

def load_state():
    try:
        with open(STATE_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except Exception:
        return {"posts":[]}

def choose_topic(all_items, state):
    posts = state.get("posts", [])
    # Vee News is now cricket-only. Prefer Indian cricket first, then other
    # cricket stories; never fall back to general/non-cricket news.
    cricket = [x for x in all_items if x["kind"]=="cricket"]
    recent = {p.get("link") for p in posts[-20:]}
    pool = [x for x in cricket if x["link"] not in recent]
    if not pool:
        pool = cricket
    return sorted(pool,key=lambda x:x["published"],reverse=True)[0] if pool else None

def simple_title(item):
    # Keep the original headline; do not machine-translate words.
    title=clean_html(item.get("title",""))
    title=re.sub(r"\s+-\s+[^-]+$","",title).strip(" -:|")
    return " ".join(title.split()[:14])

def simple_summary(item):
    if item["kind"]=="cricket":
        return "टीम इंडिया और क्रिकेट से जुड़ी यह ताजा खबर है। Vee News इस खबर पर नजर रख रहा है। नई जानकारी मिलने पर अपडेट किया जाएगा।"
    return "यह देश से जुड़ी ताजा प्रमुख खबर है। Vee News इस खबर पर नजर रख रहा है। नई जानकारी मिलने पर अपडेट किया जाएगा।"

def build_description(item):
    title=simple_title(item)
    return (
        f"📰 Vee News Update\n\n{title}\n\n"
        f"क्या हुआ?\n{simple_summary(item)}\n\n"
        f"क्यों महत्वपूर्ण है?\nयह अभी की प्रमुख अपडेट है। नई और सत्यापित जानकारी मिलने पर Vee News इसे अपडेट करेगा।\n\n"
        f"स्रोत: {item['source']}\nVee News | Contact: {PHONE}\n\n"
        f"#VeeNews #IndianCricket #TeamIndia #CricketNews #HindiNews"
    )

HINDI="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
ENG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ENG_BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(path,size):
    # Use HarfBuzz/FriBidi shaping through Pillow's RAQM engine.
    # This is required for correct Devanagari glyphs and matras in Hindi.
    return ImageFont.truetype(path,size,layout_engine=ImageFont.Layout.RAQM)

def safe_text(text):
    return re.sub(r"[^\u0900-\u097F A-Za-z0-9.,!?;:'\"()/#%&+\-–—₹|]"," ",str(text))

def _font_for_run(run,size,bold=False):
    is_hindi=any("\u0900"<=ch<="\u097F" for ch in run)
    return font(HINDI_BOLD if bold else HINDI,size) if is_hindi else font(ENG_BOLD if bold else ENG,size)

def _runs(text):
    text=safe_text(text)
    if not text: return []
    runs=[]; cur=text[0]; cur_hindi="\u0900"<=text[0]<="\u097F"
    for ch in text[1:]:
        h="\u0900"<=ch<="\u097F"
        if h==cur_hindi:
            cur+=ch
        else:
            runs.append((cur,cur_hindi)); cur=ch; cur_hindi=h
    runs.append((cur,cur_hindi))
    return runs

def mixed_width(draw,text,size,bold=False):
    total=0
    for run,_ in _runs(text):
        f=_font_for_run(run,size,bold)
        b=draw.textbbox((0,0),run,font=f)
        total+=b[2]-b[0]
    return total

def draw_mixed(draw,xy,text,size,fill,bold=False):
    x,y=xy
    for run,is_hindi in _runs(text):
        f=_font_for_run(run,size,bold)
        draw.text((x,y),run,font=f,fill=fill,language="hi" if is_hindi else None)
        x+=draw.textbbox((0,0),run,font=f)[2]

def wrap_mixed(draw,text,size,max_width,bold=False,max_lines=3):
    words=safe_text(text).split(); lines=[]; cur=""
    for word in words:
        test=word if not cur else cur+" "+word
        if mixed_width(draw,test,size,bold)<=max_width:
            cur=test
        else:
            if cur: lines.append(cur)
            cur=word
            if len(lines)>=max_lines:
                break
    if cur and len(lines)<max_lines: lines.append(cur)
    return lines[:max_lines]

def create_image(item):
    # Permanent Vee News 9:16 branded frame.
    im=Image.new("RGB",(WIDTH,HEIGHT),(7,31,76)); d=ImageDraw.Draw(im)
    navy=(7,31,76); blue=(15,67,145); red=(226,24,34); yellow=(255,211,0)
    white=(255,255,255); dark=(12,36,74); light=(246,249,253)

    d.rectangle([0,0,WIDTH,185],fill=navy)
    d.polygon([(0,175),(680,175),(760,0),(690,0)],fill=yellow)
    d.rounded_rectangle([42,32,170,160],radius=28,fill=red)
    draw_mixed(d,(70,46),"V",78,white,True)
    d.text((195,36),"Vee",font=font(ENG_BOLD,68),fill=white)
    d.text((360,36),"News",font=font(ENG_BOLD,68),fill=yellow)
    d.text((198,112),"FAST  |  TRUSTED  |  ALWAYS",font=font(ENG_BOLD,22),fill=white)
    draw_mixed(d,(735,44),"देश की हर बड़ी खबर",28,white,True)
    draw_mixed(d,(800,92),"सबसे पहले",32,yellow,True)

    d.rounded_rectangle([24,205,1056,690],radius=24,fill=blue,outline=white,width=4)
    d.ellipse([690,285,1010,605],fill=(26,104,194),outline=yellow,width=8)
    d.ellipse([760,355,940,535],fill=red,outline=white,width=6)
    d.line([790,370,910,520],fill=white,width=5); d.line([810,370,930,520],fill=white,width=5)
    draw_mixed(d,(62,250),"CRICKET NEWS",38,yellow,True)
    draw_mixed(d,(62,330),"INDIAN",62,white,True)
    draw_mixed(d,(62,405),"CRICKET",62,yellow,True)
    draw_mixed(d,(62,500),"Team India  •  Latest Update",28,white,True)

    d.polygon([(25,650),(565,650),(525,775),(0,775)],fill=red)
    d.polygon([(550,650),(1035,650),(1080,775),(520,775)],fill=yellow)
    d.text((72,674),"BREAKING",font=font(ENG_BOLD,60),fill=white)
    d.text((620,674),"NEWS",font=font(ENG_BOLD,60),fill=dark)

    d.rounded_rectangle([25,790,1055,1045],radius=20,fill=navy)
    lines=wrap_mixed(d,simple_title(item),48,960,True,3); y=820
    for line in lines:
        draw_mixed(d,(55,y),line,48,white,True); y+=58

    d.rounded_rectangle([55,1000,1025,1070],radius=16,fill=yellow)
    draw_mixed(d,(78,1012),f'{item["source"]}  •  ताजा अपडेट',25,dark,True)

    d.rounded_rectangle([25,1095,1055,1585],radius=24,fill=light)
    draw_mixed(d,(60,1135),"क्या हुआ?",36,blue,True)
    body_lines=wrap_mixed(d,simple_summary(item),28,930,False,4); y=1195
    for line in body_lines:
        draw_mixed(d,(60,y),line,28,dark,False); y+=47
    d.line([60,1480,1020,1480],fill=(200,214,235),width=2)
    draw_mixed(d,(60,1505),"Team India  |  Cricket Update",25,blue,True)
    draw_mixed(d,(700,1505),"Vee News",25,red,True)

    d.rectangle([0,1605,WIDTH,1755],fill=navy)
    draw_mixed(d,(55,1640),"Cricket  |  Team India  |  Latest Updates  |  Vee News",25,white,True)
    d.rectangle([0,1755,WIDTH,1920],fill=yellow)
    d.text((58,1790),"CONTACT US",font=font(ENG_BOLD,28),fill=dark)
    d.text((300,1780),PHONE,font=font(ENG_BOLD,46),fill=dark)
    d.rounded_rectangle([790,1775,1035,1875],radius=22,fill=red)
    d.text((820,1800),"Vee News",font=font(ENG_BOLD,28),fill=white)
    d.text((817,1840),"Always With You",font=font(ENG_BOLD,17),fill=white)
    d.rectangle([0,1908,WIDTH//3,1920],fill=(255,153,51))
    d.rectangle([WIDTH//3,1908,2*WIDTH//3,1920],fill=white)
    d.rectangle([2*WIDTH//3,1908,WIDTH,1920],fill=(19,136,8))
    im.save(OUTPUT,quality=94,optimize=True)

def post_to_facebook(caption):
    url=f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos"; boundary=uuid.uuid4().hex
    with open(OUTPUT,"rb") as f: image_data=f.read()
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'
          f'--{boundary}\r\nContent-Disposition: form-data; name="access_token"\r\n\r\n{ACCESS_TOKEN}\r\n'
          f'--{boundary}\r\nContent-Disposition: form-data; name="source"; filename="vee_news.jpg"\r\n'
          f'Content-Type: image/jpeg\r\n\r\n').encode("utf-8")+image_data+f'\r\n--{boundary}--\r\n'.encode("utf-8")
    req=urllib.request.Request(url,data=body,headers={"Content-Type":f"multipart/form-data; boundary={boundary}"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as response: return response.read().decode("utf-8")

def main():
    state=load_state()
    items=dedupe(collect(CRICKET_FEEDS,"cricket")+collect(GENERAL_FEEDS,"general"))
    item=choose_topic(items,state)
    if not item:
        print("No usable Vee News topic found; skipping this run."); return
    caption=build_description(item); create_image(item)
    print("Selected:",item["title"]); print("Category:",item["category"],"|",item["kind"])
    try:
        print("Vee News Facebook post successful:",post_to_facebook(caption))
    except urllib.error.HTTPError as e:
        print("Facebook post failed:",e.code)
        print(e.read().decode("utf-8",errors="replace")); raise
    posts=state.get("posts",[])
    posts.append({"title":item["title"],"link":item["link"],"kind":item["kind"],"source":item["source"],"posted_at":datetime.now(IST).isoformat()})
    state["posts"]=posts[-100:]
    with open(STATE_FILE,"w",encoding="utf-8") as f: json.dump(state,f,ensure_ascii=False,indent=2)

if __name__=="__main__":
    main()
