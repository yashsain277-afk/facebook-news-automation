import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OFFSET_FILE = ".github/telegram_offset.txt"
INBOX = "telegram_incoming"
ALLOWED_VIDEO = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}

def api(method, params=None):
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN secret is missing.")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "VeeNewsTelegramBridge/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode("utf-8"))
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data["result"]

def download_file(file_id, target):
    info = api("getFile", {"file_id": file_id})
    file_path = info.get("file_path")
    if not file_path:
        raise RuntimeError("Telegram did not return file_path.")
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    req = urllib.request.Request(url, headers={"User-Agent": "VeeNewsTelegramBridge/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(target, "wb") as out:
        out.write(r.read())
    return target

def load_offset():
    try:
        with open(OFFSET_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_offset(offset):
    os.makedirs(os.path.dirname(OFFSET_FILE), exist_ok=True)
    with open(OFFSET_FILE, "w", encoding="utf-8") as f:
        f.write(str(offset))

def choose_media(message):
    if message.get("photo"):
        photo = message["photo"][-1]
        return photo["file_id"], ".jpg"
    if message.get("video"):
        video = message["video"]
        filename = os.path.basename(video.get("file_name") or "telegram_video.mp4")
        ext = os.path.splitext(filename)[1].lower() or ".mp4"
        if ext not in ALLOWED_VIDEO:
            ext = ".mp4"
        return video["file_id"], ext
    if message.get("document"):
        doc = message["document"]
        filename = os.path.basename(doc.get("file_name") or "telegram_media")
        ext = os.path.splitext(filename)[1].lower()
        if ext in ALLOWED_VIDEO or ext in {".jpg", ".jpeg", ".png", ".webp"}:
            return doc["file_id"], ext
    return None, None

def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN secret is missing.")

    offset = load_offset()
    updates = api("getUpdates", {
        "offset": offset,
        "timeout": 0,
        "allowed_updates": json.dumps(["message"])
    })

    if not updates:
        print("TELEGRAM: no new messages")
        return 0

    os.makedirs(INBOX, exist_ok=True)
    newest_update = offset
    selected = None

    for update in updates:
        update_id = int(update["update_id"])
        newest_update = max(newest_update, update_id + 1)
        message = update.get("message") or {}
        file_id, ext = choose_media(message)
        if not file_id:
            continue

        caption = (message.get("caption") or "").strip()
        if not caption:
            print(f"TELEGRAM: media update {update_id} has no caption; skipped.")
            continue

        selected = (update_id, file_id, ext, caption)

    if not selected:
        save_offset(newest_update)
        print("TELEGRAM: no usable media+caption message")
        return 0

    update_id, file_id, ext, caption = selected
    media_path = os.path.join(INBOX, f"telegram_{update_id}{ext}")
    text_path = os.path.join(INBOX, f"telegram_{update_id}.txt")

    # Keep only this Telegram item as the current input.
    for name in os.listdir(INBOX):
        path = os.path.join(INBOX, name)
        if os.path.isfile(path):
            os.remove(path)

    download_file(file_id, media_path)
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(caption)

    print("TELEGRAM_INPUT_READY:", media_path)
    print("TELEGRAM_CAPTION:", caption)
    # The caller commits this offset only after the Facebook post succeeds.
    with open(".telegram_pending_offset", "w", encoding="utf-8") as f:
        f.write(str(newest_update))

    return 0

if __name__ == "__main__":
    sys.exit(main())
