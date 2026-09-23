import glob
import json
import os
import subprocess
import urllib.error
import urllib.request
import uuid

from PIL import Image

from janta_ki_awaz_frame import make_frame

PAGE_ID = os.environ["JANTA_KI_AWAZ_PAGE_ID"]
ACCESS_TOKEN = os.environ["JANTA_KI_AWAZ_PAGE_ACCESS_TOKEN"]
INPUT_DIR = os.environ.get("JANTA_INPUT_DIR", "telegram_incoming")
POSTED_FILE = os.environ.get("JANTA_TELEGRAM_POSTED_FILE", "janta_telegram_posted.json")


def load_posted():
    try:
        with open(POSTED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_posted(items):
    with open(POSTED_FILE, "w", encoding="utf-8") as f:
        json.dump(items[-100:], f, ensure_ascii=False, indent=2)


def find_media():
    files = []
    for pattern in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.mp4", "*.mov", "*.m4v", "*.webm", "*.avi", "*.mkv"):
        files.extend(glob.glob(os.path.join(INPUT_DIR, pattern)))
    return sorted(files)


def make_photo(media_path):
    ext = os.path.splitext(media_path)[1].lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        return media_path

    out = os.path.join(INPUT_DIR, "telegram_video_frame.jpg")
    subprocess.run(
        ["ffmpeg", "-y", "-i", media_path, "-frames:v", "1", "-q:v", "2", out],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out


def post_photo(image_path, caption):
    url = f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos"
    boundary = uuid.uuid4().hex

    with open(image_path, "rb") as f:
        image_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="caption"\r\n\r\n'
        f"{caption}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="access_token"\r\n\r\n'
        f"{ACCESS_TOKEN}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="source"; filename="janta_ki_awaz.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8")
    body += image_data
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def main():
    text_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.txt")))
    media_files = find_media()

    if not text_files:
        print("JANTA TELEGRAM: no caption found")
        return 0
    if not media_files:
        print("JANTA TELEGRAM: no media found")
        return 0

    caption = open(text_files[0], "r", encoding="utf-8").read().strip()
    if not caption:
        print("JANTA TELEGRAM: empty caption")
        return 0

    posted = load_posted()
    media_path = make_photo(media_files[0])
    output = "janta_ki_awaz_telegram.jpg"
    make_frame(
        headline=caption,
        source="Telegram",
        photo_path=media_path,
        output=output,
    )

    result = post_photo(output, f"📰 {caption}\n\nजनता की आवाज़ | अंता | बारां | राजस्थान")
    print("JANTA TELEGRAM: Facebook post successful")
    print(result)

    posted.append({"caption": caption})
    save_posted(posted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
