import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Hardcoded Default Proxy
DEFAULT_PROXY = "http://bwadvamb:y06rok7kerdd@31.59.20.176:6754"

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
        "message": "yt-dlp Proxy API is Running!"
    }), 200

@app.route('/extract', methods=['GET', 'POST'])
def extract_url():
    # সম্পূর্ণ ফাংশনটিকে Try-Except দিয়ে ঘিরে ফেলা হয়েছে যাতে কোনো অবস্থাতেই 500 Server Error না আসে
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

        # যদি URL না দেওয়া হয় তবে সুন্দর একটি JSON এরর মেসেজ দেবে
        if not url:
            return jsonify({
                "success": False, 
                "error": "URL parameter missing. Usage: /extract?url=YOUR_YOUTUBE_URL"
            }), 400

        active_proxy = parse_proxy_string(custom_proxy) if custom_proxy else parse_proxy_string(DEFAULT_PROXY)

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'proxy': active_proxy,
            'noplaylist': True,
            # অডিও এবং ভিডিও দুটোই আছে এমন সিঙ্গেল ফরম্যাট আনবে
            'format': '18/22/best[acodec!=none][vcodec!=none]/best',
            'socket_timeout': 15, # প্রক্সি স্লো হলে ১৫ সেকেন্ড পর টাইমআউট হয়ে এরর জানাবে
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }

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

            return jsonify({
                "success": True,
                "title": info.get('title'),
                "duration": info.get('duration'),
                "thumbnail": info.get('thumbnail'),
                "raw_stream_url": stream_url,
                "proxy_used": active_proxy,
                "all_combined_formats": formats_data
            }), 200

    except Exception as e:
        # প্রক্সি ব্লক বা প্রক্সি অফ থাকলে সেই এররটি JSON আকারে রিটার্ন করবে
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
