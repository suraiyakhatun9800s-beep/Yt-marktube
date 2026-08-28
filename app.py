import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import socket

# দ্রুত রেসপন্স নিশ্চিত করতে ২ সেকেন্ড টাইমআউট
socket.setdefaulttimeout(2)

app = Flask(__name__)
CORS(app)

API_KEY = "YT_SECURE_API_V1_2026_PRO"

# yt-dlp কনফিগারেশন
BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "noplaylist": True,
    "cachedir": False,
    "format": "best[protocol=https]/best",
    "socket_timeout": 5,
    "extractor_args": {
        "youtube": {
            "player_client": [
                "android",
                "web",
                "android_tv",
                "ios"
            ]
        }
    }
}

def extract(url):
    """সরাসরি ইউটিউব থেকে ইনফো এক্সট্রাক্ট করার ফাংশন"""
    with yt_dlp.YoutubeDL(BASE_OPTS) as ydl:
        return ydl.extract_info(url, download=False)

@app.route("/")
def home():
    return "API is Running!"

@app.route("/get-link")
def get_link():
    key = request.args.get("key")
    url = request.args.get("url")

    if key != API_KEY:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    if not url:
        return jsonify({"success": False, "error": "Missing URL"}), 400

    start = time.time()

    try:
        info = extract(url)
        return jsonify({
            "success": True,
            "mode": "direct",
            "playback": info.get("url"),
            "title": info.get("title"),
            "duration": info.get("duration"),
            "took": round(time.time() - start, 2)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Extraction failed",
            "detail": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
