import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# সাম্প্রতিক কাজের প্রক্সি (ডিফল্ট)
DEFAULT_PROXY = "http://DVSn2on8s5:h9S51gF@104.219.238.238:46671"

def parse_proxy_string(proxy_str):
    if not proxy_str:
        return None
    proxy_str = proxy_str.strip()
    protocol = "http"
    if "://" in proxy_str:
        protocol, proxy_str = proxy_str.split("://", 1)
        
    if "@" in proxy_str:
        return f"{protocol}://{proxy_str}"
        
    parts = proxy_str.split(":")
    if len(parts) == 4:
        ip, port, user, password = parts
        return f"{protocol}://{user}:{password}@{ip}:{port}"
    elif len(parts) == 2:
        ip, port = parts
        return f"{protocol}://{ip}:{port}"
        
    return f"{protocol}://{proxy_str}"

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "Ultra-light Stream Extractor API is Running"
    }), 200

@app.route('/extract', methods=['GET', 'POST'])
def extract():
    try:
        url = None
        custom_proxy = None

        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            url = data.get('url')
            custom_proxy = data.get('proxy')
        else:
            url = request.args.get('url')
            custom_proxy = request.args.get('proxy')

        if not url:
            return jsonify({"success": False, "error": "URL parameter is missing"}), 400

        active_proxy = parse_proxy_string(custom_proxy) if custom_proxy else parse_proxy_string(DEFAULT_PROXY)

        # মিনিমাল এবং ফাস্ট অপটিমাইজেশন সেটিংস
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'skip_download': True,
            'socket_timeout': 8,
            # অডিও+ভিডিও একসাথে মার্জ করা সিঙ্গেল ডিফল্ট ফাইল (Format 18/22)
            'format': '18/22/b[acodec!=none][vcodec!=none]/best',
            'proxy': active_proxy,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0 Safari/537.36',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # সরাসরি প্লে-এবল অরিজিনাল সিঙ্গেল স্ট্রিম লিংক
            stream_url = info.get('url')

            # অতি সংক্ষিপ্ত ও ক্লিন JSON রেসপন্স (CPU/RAM বাঁচানোর জন্য)
            return jsonify({
                "success": True,
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "stream_url": stream_url
            }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
