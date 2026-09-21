import os
import re
import html
import json
import uuid
import urllib.parse
import urllib.request
import urllib.error
import subprocess
from datetime import datetime, timezone, timedelta
from io import BytesIO

from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont

INPUT_DIR = os.environ.get("VEE_INPUT_DIR", "incoming_news")
WORK = "vee_upload_news_work"
OUTPUT = "vee_upload_news.mp4"
W, H = 1080, 1920
IST = timezone(timedelta(hours=5, minutes=30))
API_VERSION = "v26.0"

PAGE_ID = os.environ.get("VEE_NEWS_PAGE_ID", "")
ACCESS_TOKEN = os.environ.get("VEE_NEWS_PAGE_ACCESS_TOKEN", "")

HINDI = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
HINDI_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
ENG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ENG_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}


def clean(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(text or "")))
    return re.sub(r"\s+", " ", text).strip()


def devanagari_count(text):
    return sum(1 for ch in str(text or "") if 0x0900 <= ord(ch) <= 0x097F)


def translate_to_hindi(text):
    text = clean(text)
    if not text or devanagari_count(text) >= 3:
        return text
    try:
        params = {
            "client": "gtx", "sl": "auto", "tl": "hi", "dt": "t",
            "q": text[:1800],
        }
        url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        translated = clean("".join(part[0] for part in data[0] if part and part[0]))
        if devanagari_count(translated) >= 3:
            print("HINDI_TRANSLATION_OK")
            return translated
    except Exception as exc:
        print("Translation skipped:", exc)
    return text


def read_news_text():
    candidates = []
    for name in os.listdir(INPUT_DIR):
        path = os.path.join(INPUT_DIR, name)
        if os.path.isfile(path) and os.path.splitext(name.lower())[1] in {".txt", ".md"}:
            candidates.append(path)
    if not candidates:
        raise RuntimeError("Upload news.txt (or .md) inside incoming_news/.")
    path = max(candidates, key=os.path.getmtime)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    text = clean(text)
    if not text:
        raise RuntimeError("The news text file is empty.")
    print("NEWS_TEXT_FILE:", path)
    return text


def find_media():
    files = []
    for name in os.listdir(INPUT_DIR):
        path = os.path.join(INPUT_DIR, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(name.lower())[1]
        if ext in IMAGE_EXTS or ext in VIDEO_EXTS:
            files.append(path)
    if not files:
        raise RuntimeError("Upload one photo or video inside incoming_news/.")
    # If both exist, use the newest uploaded media.
    path = max(files, key=os.path.getmtime)
    print("MEDIA_FILE:", path)
    return path


def make_script(raw):
    raw = clean(raw)
    parts = [clean(x) for x in re.split(r"(?<=[.!?।])\s+|\n+", raw) if clean(x)]
    headline = parts[0] if parts else raw[:180]
    body = " ".join(parts[1:]) if len(parts) > 1 else raw

    headline_hi = translate_to_hindi(headline)
    body_hi = translate_to_hindi(body)

    # Keep the uploaded facts; only restructure them into a spoken bulletin.
    body_hi = re.sub(r"\s+", " ", body_hi).strip()
    if len(body_hi) > 650:
        body_hi = body_hi[:650].rsplit(" ", 1)[0] + "।"

    script = (
        "नमस्कार। आप देख रहे हैं वी न्यूज़। "
        "आज की बड़ी खबर है। "
        f"{headline_hi.strip(' ।|:-')}। "
    )
    if body_hi and body_hi != headline_hi:
        script += f"मिली जानकारी के अनुसार, {body_hi.strip(' ।|:-')}। "
    script += (
        "आगे की जानकारी सामने आने पर अपडेट किया जाएगा। "
        "ऐसी ही ताज़ा खबरों के लिए वी न्यूज़ को फॉलो करें।"
    )

    # Target a practical 30–55 second narration range.
    words = len(script.split())
    if words < 70:
        script += " खबर से जुड़े नए अपडेट के लिए हमारे अगले अपडेट पर नज़र रखें।"
    if len(script.split()) > 125:
        script = " ".join(script.split()[:125]).rstrip(" ।") + "।"

    print("NEWS_SCRIPT_WORDS:", len(script.split()))
    print("NEWS_SCRIPT:", script)
    return headline_hi, body_hi, script


def font_for(run, size, bold=False):
    has_hindi = any(0x0900 <= ord(c) <= 0x097F for c in str(run))
    path = HINDI_BOLD if has_hindi and bold else HINDI if has_hindi else ENG_BOLD if bold else ENG
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def runs(text):
    text = str(text or "")
    if not text:
        return []
    out, cur = [], text[0]
    cur_hi = 0x0900 <= ord(text[0]) <= 0x097F
    for ch in text[1:]:
        hi = 0x0900 <= ord(ch) <= 0x097F
        if hi == cur_hi:
            cur += ch
        else:
            out.append((cur, cur_hi))
            cur, cur_hi = ch, hi
    out.append((cur, cur_hi))
    return out


def mixed_width(draw, text, size, bold=False):
    return sum(draw.textbbox((0, 0), run, font=font_for(run, size, bold))[2] for run, _ in runs(text))


def draw_mixed(draw, xy, text, size, fill, bold=False):
    x, y = xy
    for run, is_hi in runs(text):
        f = font_for(run, size, bold)
        draw.text((x, y), run, font=f, fill=fill, language="hi" if is_hi else None)
        x += draw.textbbox((0, 0), run, font=f)[2]


def wrap_mixed(draw, text, size, max_width, bold=False, max_lines=3):
    words = str(text or "").split()
    lines, cur = [], ""
    for word in words:
        test = word if not cur else cur + " " + word
        if mixed_width(draw, test, size, bold) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
            if len(lines) >= max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    return lines[:max_lines]


def load_image(path):
    img = Image.open(path).convert("RGB")
    return img


def cover(img, size=(W, H)):
    w, h = size
    ratio = max(w / img.width, h / img.height)
    nw, nh = int(img.width * ratio), int(img.height * ratio)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - w) // 2, (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def make_overlays(headline, body):
    os.makedirs(WORK, exist_ok=True)
    body = body or "यह खबर अभी चर्चा में है। उपलब्ध जानकारी के आधार पर प्रमुख अपडेट सामने आया है।"

    for idx in range(3):
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay, "RGBA")
        d.rectangle([0, 0, W, 205], fill=(5, 20, 55, 235))
        d.rectangle([0, 1450, W, H], fill=(5, 20, 55, 238))
        d.rectangle([0, 0, 18, H], fill=(221, 24, 31, 255))

        d.rounded_rectangle([40, 30, 285, 118], 18, fill=(221, 24, 31, 255))
        d.text((70, 49), "VEE NEWS", font=ImageFont.truetype(ENG_BOLD, 31), fill="white")
        d.text((325, 42), "न्यूज़ अपडेट", font=ImageFont.truetype(HINDI_BOLD, 52), fill=(255, 210, 0))

        if idx == 0:
            draw_mixed(d, (55, 1495), "बड़ी खबर", 50, (255, 210, 0), True)
            y = 1570
            for line in wrap_mixed(d, headline[:180], 50, 930, True, 4):
                draw_mixed(d, (55, y), line, 50, "white", True)
                y += 64
        elif idx == 1:
            draw_mixed(d, (55, 1495), "मुख्य अपडेट", 50, (255, 210, 0), True)
            y = 1570
            for line in wrap_mixed(d, body[:360], 35, 930, False, 5):
                draw_mixed(d, (55, y), line, 35, "white", False)
                y += 50
        else:
            draw_mixed(d, (55, 1495), "वी न्यूज़", 50, (255, 210, 0), True)
            draw_mixed(d, (55, 1570), "ताज़ा न्यूज़ अपडेट", 35, "white", True)
            draw_mixed(d, (55, 1660), "ताज़ा खबरों के लिए VEE NEWS को FOLLOW करें", 31, "white", False)
            d.text((55, 1750), datetime.now(IST).strftime("%d %b %Y | %H:%M IST"),
                   font=ImageFont.truetype(ENG, 27), fill="white")

        overlay.save(os.path.join(WORK, f"overlay{idx}.png"))


def make_voice(script):
    path = os.path.join(WORK, "voice.mp3")
    gTTS(text=script, lang="hi", slow=False).save(path)
    print("VOICE_CREATED:", path)


def make_photo_background(media_path):
    img = load_image(media_path)
    img = cover(img)
    out = os.path.join(WORK, "background.mp4")
    # 45 seconds of the uploaded photo, with a very slow zoom.
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", media_path,
        "-t", "45",
        "-vf", "scale=1200:-2,zoompan=z='min(zoom+0.0005,1.12)':d=1:s=1080x1920:fps=30,setsar=1",
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
        "-pix_fmt", "yuv420p", out
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        # Fallback if zoompan is unavailable/problematic.
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", media_path, "-t", "45",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
            "-pix_fmt", "yuv420p", out
        ]
        subprocess.run(cmd, check=True)
    return out


def make_video_background(media_path):
    out = os.path.join(WORK, "background.mp4")
    # Uploaded video is the main footage; audio is replaced by the Vee News narration.
    cmd = [
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", media_path, "-t", "45",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
        "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
        "-pix_fmt", "yuv420p", out
    ]
    subprocess.run(cmd, check=True)
    return out


def compose_video(background):
    out = os.path.join(WORK, "final_no_facebook.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", background,
        "-i", os.path.join(WORK, "voice.mp3"),
        "-loop", "1", "-i", os.path.join(WORK, "overlay0.png"),
        "-loop", "1", "-i", os.path.join(WORK, "overlay1.png"),
        "-loop", "1", "-i", os.path.join(WORK, "overlay2.png"),
        "-filter_complex",
        "[0:v]trim=start=0:end=15,setpts=PTS-STARTPTS[v0];"
        "[0:v]trim=start=15:end=30,setpts=PTS-STARTPTS[v1];"
        "[0:v]trim=start=30:end=45,setpts=PTS-STARTPTS[v2];"
        "[v0][2:v]overlay=0:0:enable='between(t,0,15)'[o0];"
        "[v1][3:v]overlay=0:0:enable='between(t,0,15)'[o1];"
        "[v2][4:v]overlay=0:0:enable='between(t,0,15)'[o2];"
        "[o0][o1][o2]concat=n=3:v=1:a=0[v]",
        "-map", "[v]", "-map", "1:a",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,atempo=1.08",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
        "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p",
        "-shortest", "-movflags", "+faststart", out
    ]
    subprocess.run(cmd, check=True)
    return out


def caption(headline):
    title = clean(headline)
    return (
        f"🏏 Vee News | News Update\n\n{title}\n\n"
        "#VeeNews #NewsUpdate #HindiNews #BreakingNews"
    )


def post_video(video_path, title_text):
    if not PAGE_ID or not ACCESS_TOKEN:
        raise RuntimeError("VEE_NEWS_PAGE_ID / VEE_NEWS_PAGE_ACCESS_TOKEN secret is missing.")

    url = f"https://graph-video.facebook.com/{API_VERSION}/{PAGE_ID}/videos"
    boundary = uuid.uuid4().hex

    with open(video_path, "rb") as f:
        video_data = f.read()

    fields = [
        ("access_token", ACCESS_TOKEN),
        ("title", clean(title_text)[:80]),
        ("description", caption(title_text)[:500]),
        ("published", "true"),
    ]

    chunks = []
    for name, value in fields:
        chunks.append(
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"{name}\"\r\n\r\n"
            f"{value}\r\n"
        .encode("utf-8"))
    chunks.append(
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"source\"; filename=\"vee_news.mp4\"\r\n"
        f"Content-Type: video/mp4\r\n\r\n".encode("utf-8")
    )
    chunks.append(video_data)
    chunks.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    body = b"".join(chunks)
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            result = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print("FACEBOOK_VIDEO_ERROR:", detail)
        raise
    print("FACEBOOK_VIDEO_POST_OK:", result)
    return result


def main():
    os.makedirs(WORK, exist_ok=True)
    raw = read_news_text()
    media = find_media()

    headline, body, script = make_script(raw)
    with open(os.path.join(WORK, "script.txt"), "w", encoding="utf-8") as f:
        f.write(script)

    make_overlays(headline, body)
    make_voice(script)

    ext = os.path.splitext(media.lower())[1]
    if ext in IMAGE_EXTS:
        background = make_photo_background(media)
    else:
        background = make_video_background(media)

    final = compose_video(background)
    subprocess.run(["cp", final, OUTPUT], check=True)

    # Check final duration and file size before attempting Facebook upload.
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-of", "default=noprint_wrappers=1:nokey=1", OUTPUT
    ], text=True).strip().splitlines()
    print("FINAL_DURATION_SECONDS:", probe[0] if probe else "unknown")
    print("FINAL_SIZE_BYTES:", probe[1] if len(probe) > 1 else "unknown")

    post_video(OUTPUT, headline)
    print("UPLOAD_COMPLETE")


if __name__ == "__main__":
    main()
