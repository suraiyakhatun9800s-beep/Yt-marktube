import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
# App ও Website যেকোনো জায়গা থেকে API কল করার জন্য CORS এনাবল করা হলো
CORS(app) 

# -------------------------------------------------------------------
# আপনার দেওয়া ডাইরেক্ট প্রক্সি (Hardcoded Default Proxy)
# -------------------------------------------------------------------
DEFAULT_PROXY = "http://bwadvamb:y06rok7kerdd@31.59.20.176:6754"

def parse_proxy_string(proxy_str):
    """
    বিভিন্ন ফর্ম্যাটের প্রক্সি স্ট্রিংকে yt-dlp এর জন্য স্ট্যান্ডার্ড URL-এ রূপান্তর করে।
    সাপোর্টেড ফর্ম্যাট:
    - protocol://user:pass@ip:port
    - protocol://ip:port:user:pass
    - user:pass@ip:port
    - ip:port:user:pass
    - ip:port
    """
    if not proxy_str:
        return None
        
    proxy_str = proxy_str.strip()
    
    protocol = "http"
    if "://" in proxy_str:
        protocol, proxy_str = proxy_str.split("://", 1)
        
    # Standard format: user:pass@ip:port
    if "@" in proxy_str:
        return f"{protocol}://{proxy_str}"
        
    parts = proxy_str.split(":")
    
    # Format: ip:port:user:pass
    if len(parts) == 4:
        ip, port, user, password = parts
        return f"{protocol}://{user}:{password}@{ip}:{port}"
        
    # Format: ip:port
    elif len(parts) == 2:
        ip, port = parts
        return f"{protocol}://{ip}:{port}"
        
    return f"{protocol}://{proxy_str}"

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "message": "yt-dlp Direct Proxy Extractor API is Running!"
    }), 200

@app.route('/extract', methods=['GET', 'POST'])
def extract_url():
    # GET এবং POST দুটো রিকুয়েস্টই ইনপুট নেবে
    if request.method == 'POST':
        data = request.get_json() or {}
        url = data.get('url')
        custom_proxy = data.get('proxy')
    else:
        url = request.args.get('url')
        custom_proxy = request.args.get('proxy')

    if not url:
        return jsonify({"success": False, "error": "URL field is required"}), 400

    # ইউজার প্রক্সি না পাঠালে কোডের ভেতরের DEFAULT_PROXY কাজ করবে
    if custom_proxy:
        active_proxy = parse_proxy_string(custom_proxy)
    else:
        active_proxy = parse_proxy_string(DEFAULT_PROXY)

    # yt-dlp কনফিগারেশন
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'proxy': active_proxy  # ডাইরেক্ট প্রক্সি এখানে সেট হচ্ছে
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # সরাসরি প্লে-এবল অরিজিনাল মেইন স্ট্রিম URL
            stream_url = info.get('url')
            
            # প্রয়োজনে সব ধরনের রেজোলিউশনের আলাদা স্ট্রিম URL
            formats_data = []
            if 'formats' in info:
                for f in info['formats']:
                    formats_data.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution'),
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
                "all_formats": formats_data
            }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
