import os
import time
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

API_KEY = "YT_SECURE_API_V1_2026_PRO"

# আপনার কার্যকরী প্রক্সি তালিকা (IP Block বাইপাস করার জন্য)
PROXIES_LIST = [
    "http://DVSn2on8s5:h9S51gF@104.219.238.238:46671",
    "http://DVSoushlwv:pYFLHug@172.93.103.121:45727",
    "http://bwadvamb:y06rok7kerdd@31.59.20.176:6754",
    "http://bwadvamb:y06rok7kerdd@45.38.107.97:6014",
    "http://bwadvamb:y06rok7kerdd@198.105.121.200:6462"
]

def get_ytdlp_options(proxy=None):
    """yt-dlp কনফিগারেশন সেটিংস"""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "cachedir": False,
        # অডিও+ভিডিও একসাথে থাকা সিঙ্গেল ফাইল বেছে নেওয়ার রুল
        "format": "18/22/best[acodec!=none][vcodec!=none]/best[protocol=https]/best",
        "socket_timeout": 8,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0 Safari/537.36",
        }
    }
    if proxy:
        opts["proxy"] = proxy
    return opts

def extract_media(url, proxy=None):
    """ইউটিউবসহ যেকোনো মিডিয়ার জন্য এক্সট্র্যাক্টর"""
    opts = get_ytdlp_options(proxy)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # সরাসরি প্লে-এবল URL বের করা
        stream_url = info.get("url")
        
        # ব্যাকআপ লুপ
        if not stream_url and "formats" in info:
            combined = [f for f in info["formats"] if f.get("url") and f.get("vcodec") != "none" and f.get("acodec") != "none"]
            if combined:
                stream_url = combined[0].get("url")
            else:
                valid_urls = [f.get("url") for f in info["formats"] if f.get("url")]
                if valid_urls:
                    stream_url = valid_urls[-1]
                    
        return {
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "site": info.get("extractor_key") or info.get("extractor"),
            "playback": stream_url
        }

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "message": "Render Multi-Media Proxy Extractor API is Running!"
    }), 200

@app.route("/get-link", methods=["GET", "POST"])
def get_link():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        key = data.get("key")
        url = data.get("url")
        custom_proxy = data.get("proxy")
    else:
        key = request.args.get("key")
        url = request.args.get("url")
        custom_proxy = request.args.get("proxy")

    if key != API_KEY:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    if not url:
        return jsonify({"success": False, "error": "Missing URL parameter"}), 400

    start = time.time()

    # প্রক্সি তালিকা প্রস্তুত করা
    if custom_proxy:
        proxies_to_try = [custom_proxy]
    else:
        proxies_to_try = list(PROXIES_LIST)
        random.shuffle(proxies_to_try) # র‍্যান্ডম ঘুরিয়ে ফিরিয়ে ট্রাই করবে

    # ইউটিউব বা অন্য প্ল্যাটফর্মের ক্ষেত্রে প্রক্সি দিয়ে ট্রাই করা
    last_error = None
    for proxy in proxies_to_try[:3]: # সর্বোচ্চ ৩টি প্রক্সি চেষ্টা করবে
        try:
            media_data = extract_media(url, proxy)
            return jsonify({
                "success": True,
                "mode": "proxy",
                "proxy_used": proxy,
                "site": media_data["site"],
                "title": media_data["title"],
                "duration": media_data["duration"],
                "thumbnail": media_data["thumbnail"],
                "playback": media_data["playback"],
                "took": round(time.time() - start, 2)
            }), 200
        except Exception as e:
            last_error = str(e)
            continue

    # প্রক্সি কাজ না করলে শেষ চেষ্টা ডাইরেক্ট সংযোগ দিয়ে
    try:
        media_data = extract_media(url, None)
        return jsonify({
            "success": True,
            "mode": "direct",
            "site": media_data["site"],
            "title": media_data["title"],
            "duration": media_data["duration"],
            "thumbnail": media_data["thumbnail"],
            "playback": media_data["playback"],
            "took": round(time.time() - start, 2)
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Extraction failed on all attempts",
            "detail": f"Proxy Error: {last_error} | Direct Error: {str(e)}"
        }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
