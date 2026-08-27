import os
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# আপনার প্রদত্ত প্রক্সি পুল
PROXIES_LIST = [
    "http://bwadvamb:y06rok7kerdd@31.59.20.176:6754",
    "http://bwadvamb:y06rok7kerdd@45.38.107.97:6014",
    "http://bwadvamb:y06rok7kerdd@198.105.121.200:6462",
    "http://bwadvamb:y06rok7kerdd@64.137.96.74:6641",
    "http://bwadvamb:y06rok7kerdd@198.23.243.226:6361",
    "http://bwadvamb:y06rok7kerdd@38.154.185.97:6370",
    "http://bwadvamb:y06rok7kerdd@84.247.60.125:6095",
    "http://bwadvamb:y06rok7kerdd@142.111.67.146:5611",
    "http://bwadvamb:y06rok7kerdd@191.96.254.138:6185",
    "http://bwadvamb:y06rok7kerdd@31.58.9.4:6077"
]

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

def extract_media_info(url, proxy_url=None):
    # যেকোনো প্ল্যাটফর্মের জন্য ইউনিভার্সাল অপশন
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'socket_timeout': 6,
        'skip_download': True,
        # যেকোনো মিডিয়া সাইটের জন্য ফ্লেক্সিবল ফরম্যাট সিলেক্টর
        'format': 'bestvideo+bestaudio/best/b',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        }
    }
    
    if proxy_url:
        ydl_opts['proxy'] = proxy_url

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # মেইন স্ট্রিম ডাইরেক্ট লিঙ্ক
        stream_url = info.get('url')
        
        formats_data = []
        if 'formats' in info:
            for f in info['formats']:
                u = f.get('url')
                if u:
                    formats_data.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution') or f.get('format_note'),
                        'vcodec': f.get('vcodec'),
                        'acodec': f.get('acodec'),
                        'url': u
                    })
            if not stream_url and formats_data:
                stream_url = formats_data[-1]['url']

        return {
            "success": True,
            "site": info.get('extractor_key') or info.get('extractor'),
            "title": info.get('title'),
            "duration": info.get('duration'),
            "thumbnail": info.get('thumbnail'),
            "stream_url": stream_url,
            "proxy_used": proxy_url if proxy_url else "Direct Connection",
            "all_formats": formats_data
        }

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "Universal Multi-Media Extractor API is active!"
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
            return jsonify({
                "success": False,
                "error": "URL missing! Pass url parameter: /extract?url=YOUR_VIDEO_URL"
            }), 400

        # প্রক্সি সিলেকশন logic
        if custom_proxy:
            active_proxy = parse_proxy_string(custom_proxy)
        else:
            active_proxy = parse_proxy_string(random.choice(PROXIES_LIST))

        # ১ম চেষ্টা: প্রক্সি দিয়ে
        try:
            res = extract_media_info(url, active_proxy)
            return jsonify(res), 200
        except Exception as p_err:
            # ২য় চেষ্টা: প্রক্সি টাইমআউট হলে ডাইরেক্ট সার্ভার IP দিয়ে (Auto-Fallback)
            try:
                res = extract_media_info(url, None)
                return jsonify(res), 200
            except Exception as d_err:
                return jsonify({
                    "success": False,
                    "error": f"Proxy Error: {str(p_err)} | Direct Connection Error: {str(d_err)}"
                }), 200

    except Exception as global_err:
        return jsonify({
            "success": False,
            "error": str(global_err)
        }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
