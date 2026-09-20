# Vee News Upload Automation

Upload one news text file and one photo/video into `incoming_news/`.

Supported text:
- `news.txt`
- `news.md`

Supported media:
- Photos: jpg, jpeg, png, webp
- Videos: mp4, mov, m4v, webm, avi, mkv

When files are pushed to `incoming_news/`, GitHub Actions will:
1. read the uploaded news material,
2. turn it into a concise Hindi news script,
3. create Hindi voice-over,
4. use the uploaded photo/video as the main footage,
5. create a vertical 1080x1920 news video,
6. post the finished MP4 to the Vee News Facebook Page.

Keep uploaded media below GitHub's per-file repository limit. For regular video use, short/small clips are recommended.

Important: upload the text file and media together in the same GitHub commit so the workflow has both inputs on its first run.
