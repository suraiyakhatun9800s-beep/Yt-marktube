import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# আপডেট করা প্রক্সি
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
        "message": "Direct Stream Extractor API is Active!"
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

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'skip_download': True,
            'socket_timeout': 10,
            'proxy': active_proxy,
            # ১. প্রথমে অডিও+ভিডিও মার্জ ফরম্যাট (18/22) খুঁজবে
            # ২. না পেলে যেকোনো অডিও+ভিডিও যুক্ত স্ট্রিম নেবে
            # ৩. সেটিও না থাকলে বেস্ট এভেলেবল সিঙ্গেল স্ট্রিম আনবে (কোনো এরর দেবে না)
            'format': '18/22/b[acodec!=none][vcodec!=none]/best[acodec!=none][vcodec!=none]/b/best',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0 Safari/537.36',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            stream_url = info.get('url')

            # যদি কোনো কারণে ডাইরেক্ট লিঙ্ক না মেলে, ব্যাকআপ লুপ থেকে সরাসরিgooglevideo-র লিঙ্ক বের করবে
            if not stream_url and 'formats' in info:
                # অডিও এবং ভিডিও দুটোই আছে এমন লিঙ্ক ফিল্টার
                combined = [f for f in info['formats'] if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                if combined:
                    stream_url = combined[0].get('url') # ডিফল্ট কম্বাইন্ড লিঙ্ক
                else:
                    # ব্যাকআপ: যেকোনো সচল ভিডিও লিঙ্ক
                    valid_urls = [f.get('url') for f in info['formats'] if f.get('url')]
                    if valid_urls:
                        stream_url = valid_urls[-1]

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
