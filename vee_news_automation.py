import os
import json
import re
import html
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from io import BytesIO
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

def extract_image_url(entry):
    candidates = []
    for key in ("media_content", "media_thumbnail"):
        for media in entry.get(key, []) or []:
            if isinstance(media, dict) and media.get("url"):
                candidates.append(media["url"])
    for link in entry.get("links", []) or []:
        if isinstance(link, dict) and link.get("href") and str(link.get("type","")).startswith("image/"):
            candidates.append(link["href"])
    summary = str(entry.get("summary","") or entry.get("description","") or "")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary, flags=re.I)
    if m:
        candidates.append(html.unescape(m.group(1)))
    return candidates[0] if candidates else ""

def article_image_url(link):
    if not link:
        return ""
    try:
        req = urllib.request.Request(
            link,
            headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/153 Safari/537.36"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read(500000)
        text = data.decode("utf-8", errors="ignore")
        for pattern in (
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        ):
            m = re.search(pattern, text, flags=re.I)
            if m:
                return html.unescape(m.group(1))
    except Exception:
        pass
    return ""

def collect(feeds, kind):
    out = []
    for category, url in feeds.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:12]:
            title = clean_html(entry.get("title", ""))
            link = entry.get("link", "")
            if not title or not link: continue
            summary = clean_html(entry.get("summary", "") or entry.get("description", ""))
            image_url = extract_image_url(entry)
            if not image_url:
                image_url = article_image_url(link)
            out.append({"title":title,"link":link,"source":source_of(entry),
                        "summary":summary,"published":published_of(entry),
                        "image_url":image_url,
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
    summary = clean_html(item.get("summary",""))
    if summary:
        return " ".join(summary.split())[:420]
    return "टीम इंडिया और क्रिकेट से जुड़ी यह ताजा खबर है। Vee News इस खबर पर नजर रख रहा है।"

def build_description(item):
    title=simple_title(item)
    return (
        f"🏏 Vee News Cricket Update\n\n{title}\n\n"
        f"{simple_summary(item)}\n\n"
        f"स्रोत: {item['source']}\n"
        f"Vee News | Contact: {PHONE}\n\n"
        f"#VeeNews #CricketNews #IndianCricket #TeamIndia #HindiNews"
    )

HINDI="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD="/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
ENG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ENG_BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(path,size):
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
            if len(lines)>=max_lines: break
    if cur and len(lines)<max_lines: lines.append(cur)
    return lines[:max_lines]

def load_news_photo(item):
    url=item.get("image_url","")
    if not url:
        return None
    try:
        req=urllib.request.Request(
            url,
            headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/153 Safari/537.36"}
        )
        with urllib.request.urlopen(req,timeout=20) as response:
            data=response.read(8*1024*1024)
        photo=Image.open(BytesIO(data)).convert("RGB")
        return photo
    except Exception as e:
        print("News photo unavailable:",e)
        return None

def crop_cover(photo,size):
    w,h=size
    src_ratio=photo.width/photo.height
    dst_ratio=w/h
    if src_ratio>dst_ratio:
        new_h=h
        new_w=int(h*src_ratio)
    else:
        new_w=w
        new_h=int(w/src_ratio)
    photo=photo.resize((new_w,new_h),Image.Resampling.LANCZOS)
    left=(new_w-w)//2; top=(new_h-h)//2
    return photo.crop((left,top,left+w,top+h))

def create_image(item):
    # Permanent Vee News 9:16 cricket-news format inspired by the approved reference.
    im=Image.new("RGB",(WIDTH,HEIGHT),(6,24,67)); d=ImageDraw.Draw(im)
    navy=(6,24,67); blue=(18,76,157); red=(221,24,31); yellow=(255,210,0)
    white=(255,255,255); dark=(14,28,55); light=(247,249,252)

    d.rectangle([0,0,WIDTH,185],fill=navy)
    d.polygon([(0,0),(300,0),(240,185),(0,185)],fill=(18,91,190))
    d.rounded_rectangle([35,30,175,165],radius=28,fill=red,outline=yellow,width=4)
    draw_mixed(d,(62,49),"Vee",45,white,True)
    d.text((62,101),"NEWS",font=font(ENG_BOLD,30),fill=yellow)
    draw_mixed(d,(210,38),"क्रिकेट न्यूज़",55,white,True)
    draw_mixed(d,(214,108),"सच के साथ, हर कदम",27,white,True)
    d.rounded_rectangle([855,30,1040,150],radius=18,fill=yellow)
    d.text((882,48),"CRICKET",font=font(ENG_BOLD,26),fill=dark)
    d.text((897,88),"UPDATE",font=font(ENG_BOLD,25),fill=dark)

    photo=load_news_photo(item)
    if photo:
        photo=crop_cover(photo,(1030,630))
        im.paste(photo,(25,205))
        d=ImageDraw.Draw(im)
        d.rectangle([25,205,1055,835],outline=white,width=5)
    else:
        d.rounded_rectangle([25,205,1055,835],radius=22,fill=blue,outline=white,width=5)
        draw_mixed(d,(95,340),"CRICKET",92,yellow,True)
        draw_mixed(d,(95,450),"NEWS",92,white,True)
        draw_mixed(d,(95,570),"TEAM INDIA",48,white,True)

    d.polygon([(25,820),(1055,820),(1030,1085),(50,1085)],fill=red)
    draw_mixed(d,(62,845),"ब्रेकिंग न्यूज़",34,yellow,True)
    title_lines=wrap_mixed(d,simple_title(item),52,930,True,3)
    y=895
    for line in title_lines:
        draw_mixed(d,(62,y),line,52,white,True); y+=62

    d.rounded_rectangle([55,1095,1025,1165],radius=15,fill=yellow)
    stamp=datetime.now(IST).strftime("%d %b %Y | %H:%M IST")
    draw_mixed(d,(78,1110),f"{item['source']}  •  {stamp}",24,dark,True)

    d.rounded_rectangle([25,1190,1055,1615],radius=24,fill=light)
    draw_mixed(d,(58,1230),"मुख्य अपडेट",38,blue,True)
    body=wrap_mixed(d,simple_summary(item),30,930,False,6)
    y=1295
    for line in body:
        draw_mixed(d,(58,y),line,30,dark,False); y+=50
    d.line([58,1550,1022,1550],fill=(198,211,232),width=2)
    draw_mixed(d,(58,1570),"स्रोत के आधार पर अपडेट • Vee News",24,blue,True)

    d.rectangle([0,1635,WIDTH,1810],fill=navy)
    draw_mixed(d,(55,1670),"भारतीय क्रिकेट की हर बड़ी खबर",34,white,True)
    draw_mixed(d,(55,1725),"Team India  •  Cricket  •  Latest Updates",25,yellow,True)
    d.rounded_rectangle([765,1670,1035,1775],radius=22,fill=red)
    d.text((815,1694),"Vee News",font=font(ENG_BOLD,28),fill=white)
    d.text((812,1734),"सच के साथ",font=font(HINDI_BOLD,22),fill=white)

    d.rectangle([0,1810,WIDTH,1920],fill=yellow)
    d.text((58,1830),"VEE NEWS",font=font(ENG_BOLD,34),fill=dark)
    d.text((300,1830),PHONE,font=font(ENG_BOLD,34),fill=dark)
    d.rectangle([0,1906,WIDTH//3,1920],fill=(255,153,51))
    d.rectangle([WIDTH//3,1906,2*WIDTH//3,1920],fill=white)
    d.rectangle([2*WIDTH//3,1906,WIDTH,1920],fill=(19,136,8))
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
