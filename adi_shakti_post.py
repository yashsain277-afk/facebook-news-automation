import json, os, sys, uuid, urllib.request, urllib.error, subprocess
from adi_shakti_content import STORIES, HASHTAGS

PAGE_ID = os.environ["FB_PAGE_ID"]
ACCESS_TOKEN = os.environ["FB_PAGE_ACCESS_TOKEN"]
POSTED_FILE = os.environ.get("POSTED_FILE", "adi_shakti_posted.json")
PAGE_NAME = os.environ.get("PAGE_NAME", "आदि शक्ति")

try:
    with open(POSTED_FILE, "r", encoding="utf-8") as f:
        posted = json.load(f)
except Exception:
    posted = []

used = set(posted)
story = next((s for s in STORIES if s["title"] not in used), STORIES[len(posted) % len(STORIES)])
print("Selected:", story["title"])

payload = json.dumps(story, ensure_ascii=False)
subprocess.run(["python", "adi_shakti_image.py", payload], check=True)

caption = (
    f"🌺 {PAGE_NAME} 🌺\n\n"
    f"📖 {story['title']}\n\n"
    f"{story['text']}\n\n"
    f"🙏 जय माता दी 🙏\n\n"
    f"{HASHTAGS}"
)

url = f"https://graph.facebook.com/v26.0/{PAGE_ID}/photos"
boundary = uuid.uuid4().hex
with open("adi_shakti_image.jpg", "rb") as f:
    image_data = f.read()

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="caption"\r\n\r\n'
    f"{caption}\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="access_token"\r\n\r\n'
    f"{ACCESS_TOKEN}\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="source"; filename="adi_shakti_image.jpg"\r\n'
    f"Content-Type: image/jpeg\r\n\r\n"
).encode("utf-8") + image_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=60) as response:
        print("Facebook post successful:", response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("Facebook post failed:", e.code)
    print(e.read().decode("utf-8", errors="replace"))
    raise

posted.append(story["title"])
posted = posted[-len(STORIES):]
with open(POSTED_FILE, "w", encoding="utf-8") as f:
    json.dump(posted, f, ensure_ascii=False, indent=2)
