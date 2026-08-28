import os
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# প্রক্সি তালিকা
PROXIES_LIST = [
    
    "http://DVS25iznwm:fpyJa6O@136.148.66.10:34347"
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
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        # ফ্রি/স্লো প্রক্সির জন্য টাইমআউট ৩ সেকেন্ডে রাখা হয়েছে
        'socket_timeout': 20,
        'skip_download': True,
        
        # yt-dlp এর অফিসিয়াল স্ট্যান্ডার্ড কম্বাইন্ড অডিও+ভিডিও ফরম্যাট সিলেক্টর
        'format': "format": "best[protocol=https]/best",
        
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        }
    }
    
    if proxy_url:
        ydl_opts['proxy'] = proxy_url

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        stream_url = info.get('url')
        
        # অডিও ও ভিডিও দুটিই ব্যাকআপ হিসেবে ফিল্টার করার লজিক
        if not stream_url and 'formats' in info:
            for f in info['formats']:
                if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    stream_url = f.get('url')
                    break

        return {
            "success": True,
            "site": info.get('extractor_key') or info.get('extractor'),
            "title": info.get('title'),
            "duration": info.get('duration'),
            "thumbnail": info.get('thumbnail'),
            "stream_url": stream_url,
            "proxy_used": proxy_url if proxy_url else "Direct Connection"
        }

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "Fast Proxy Handling yt-dlp Extractor API"
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
                "error": "URL parameter missing"
            }), 400

        # কাস্টম প্রক্সি থাকলে সেটা নেবে, না থাকলে পুল থেকে র‍্যান্ডম প্রক্সি তৈরি করবে
        if custom_proxy:
            proxies_to_try = [parse_proxy_string(custom_proxy)]
        else:
            shuffled_proxies = list(PROXIES_LIST)
            random.shuffle(shuffled_proxies)
            # সর্বোচ্চ ৩টি ভিন্ন প্রক্সি চেষ্টা করবে যাতে অতিরিক্ত সময় নষ্ট না হয়
            proxies_to_try = [parse_proxy_string(p) for p in shuffled_proxies[:3]]

        last_proxy_error = None

        # ১. প্রক্সি দিয়ে একের পর এক দ্রুত চেষ্টা (Fast Loop)
        for active_proxy in proxies_to_try:
            try:
                res = extract_media_info(url, active_proxy)
                return jsonify(res), 200
            except Exception as p_err:
                last_proxy_error = str(p_err)
                continue # প্রক্সি স্লো বা ডেড হলে সঙ্গে সঙ্গে পরের প্রক্সিতে যাবে

        # ২. সব প্রক্সি স্লো/ফেইল হলে ডাইরেক্ট সংযোগ দিয়ে চেষ্টা
        try:
            res = extract_media_info(url, None)
            return jsonify(res), 200
        except Exception as d_err:
            return jsonify({
                "success": False,
                "error": f"Proxy Error: {last_proxy_error} | Direct Connection Error: {str(d_err)}"
            }), 200

    except Exception as global_err:
        return jsonify({
            "success": False,
            "error": str(global_err)
        }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
