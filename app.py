import os
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# আপনার প্রদান করা প্রক্সি লিস্ট (IP, Port, Username, Password)
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

def extract_with_ytdlp(url, proxy_url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'socket_timeout': 8, # দ্রুত প্রক্সি রেসপন্স পাওয়ার টাইমআউট
        'format': '18/22/best[acodec!=none][vcodec!=none]/best',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
    }
    
    if proxy_url:
        ydl_opts['proxy'] = proxy_url

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        stream_url = info.get('url')
        if not stream_url and 'formats' in info:
            for f in info['formats']:
                if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    stream_url = f.get('url')
                    break

        formats_data = []
        if 'formats' in info:
            for f in info['formats']:
                if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    formats_data.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution') or f.get('format_note'),
                        'vcodec': f.get('vcodec'),
                        'acodec': f.get('acodec'),
                        'url': f.get('url')
                    })

        return {
            "success": True,
            "title": info.get('title'),
            "duration": info.get('duration'),
            "thumbnail": info.get('thumbnail'),
            "raw_stream_url": stream_url,
            "proxy_used": proxy_url if proxy_url else "Direct Connection",
            "all_combined_formats": formats_data
        }

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "yt-dlp Multi-Proxy Rotation API is Active!"
    }), 200

@app.route('/extract', methods=['GET', 'POST'])
def extract_url():
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
            "error": "URL missing! Example: /extract?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }), 400

    # কাস্টম প্রক্সি থাকলে সেটি প্রাধান্য পাবে, নতুবা প্রক্সি পুল র্যান্ডমাইজ হবে
    if custom_proxy:
        proxies_to_try = [parse_proxy_string(custom_proxy)]
    else:
        proxies_to_try = list(PROXIES_LIST)
        random.shuffle(proxies_to_try) # র‍্যান্ডম প্রক্সি রোটেশন

    # প্রক্সিগুলোর মাধ্যমে পর্যায়ক্রমে ট্রাই করা (Proxy Fallback Loop)
    errors = []
    for proxy in proxies_to_try:
        try:
            res = extract_with_ytdlp(url, proxy)
            return jsonify(res), 200
        except Exception as e:
            errors.append(f"Proxy ({proxy}) failed: {str(e)}")
            continue

    # সব প্রক্সি ফেল করলে শেষ চেষ্টা সার্ভারের নিজস্ব IP দিয়ে
    try:
        res = extract_with_ytdlp(url, None)
        return jsonify(res), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "All proxy options failed.",
            "details": errors
        }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
