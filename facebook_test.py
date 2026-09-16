import os
import urllib.parse
import urllib.request

PAGE_ID = os.environ["FB_PAGE_ID"]
ACCESS_TOKEN = os.environ["FB_PAGE_ACCESS_TOKEN"]

message = "यह Veena News की Facebook automation test post है।"

url = f"https://graph.facebook.com/v26.0/{PAGE_ID}/feed"

data = urllib.parse.urlencode({
    "message": message,
    "access_token": ACCESS_TOKEN,
}).encode("utf-8")

request = urllib.request.Request(
    url,
    data=data,
    method="POST"
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        result = response.read().decode("utf-8")

    print("Facebook response:")
    print(result)

except Exception as e:
    print("Facebook post failed:")
    print(e)
