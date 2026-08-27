import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
# App ও Website যেকোনো জায়গা থেকে API কল করার জন্য CORS অন রাখা হয়েছে
CORS(app) 

# -------------------------------------------------------------------
# আপনার দেওয়া ডাইরেক্ট প্রক্সি (Hardcoded Default Proxy)
# -------------------------------------------------------------------
DEFAULT_PROXY = "http://bwadvamb:y06rok7kerdd@31.59.20.176:6754"

def parse_proxy_string(proxy_str):
    """
    বিভিন্ন ফর্ম্যাটের প্রক্সি স্ট্রিংকে yt-dlp এর জন্য স্ট্যান্ডার্ড URL-এ রূপান্তর করে।
    """
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
        "message": "yt-dlp Direct Combined Stream API is Running!"
    }), 200

@app.route('/extract', methods=['GET', 'POST'])
def extract_url():
    if request.method == 'POST':
        data = request.get_json() or {}
        url = data.get('url')
        custom_proxy = data.get('proxy')
    else:
        url = request.args.get('url')
        custom_proxy = request.args.get('proxy')

    if not url:
        return jsonify({"success": False, "error": "URL field is required"}), 400

    active_proxy = parse_proxy_string(custom_proxy) if custom_proxy else parse_proxy_string(DEFAULT_PROXY)

    # ইউটিউবের অডিও+ভিডিও এক সাথে থাকা ডিফল্ট ফরম্যাট অপশন
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'proxy': active_proxy,
        'noplaylist': True,
        # 18 (360p mp4 combined), 22 (720p mp4 combined) বা যেকোনো সিঙ্গেল অডিও+ভিডিও ফাইল
        'format': '18/22/b[acodec!=none][vcodec!=none]/best[acodec!=none][vcodec!=none]',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # সরাসরি অডিও+ভিডিও কম্বাইন্ড প্লে-এবল URL
            stream_url = info.get('url')
            
            # ব্যাকআপ হিসেবে যদি কোনো কারণে মূল লিঙ্ক না আসে
            if not stream_url and 'formats' in info:
                for f in info['formats']:
                    # যেসব ফরম্যাটে অডিও ও ভিডিও দুটোই আছে
                    if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        stream_url = f.get('url')

            formats_data = []
            if 'formats' in info:
                for f in info['formats']:
                    # শুধু অডিও+ভিডিও একসাথে আছে এমন ফরম্যাটগুলো ফিল্টার করবে
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
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
