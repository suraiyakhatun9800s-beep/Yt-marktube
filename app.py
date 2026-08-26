import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import Client, create_client
import yt_dlp

app = Flask(__name__)
CORS(app)

# ======================
# CONFIG & SUPABASE
# ======================
API_KEY = "YT_SECURE_API_V1_2026_PRO"

SUPABASE_URL = "https://xzwbejlxdjixndvrwvey.supabase.co"
SUPABASE_KEY = "sb_publishable_UXzBvtY5Javvg5DwaS1l6g_OUC18jr5"

# Supabase Client initialisation with timeout check
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabase Init Error: {e}")


def mark_as_dead(proxy_ip):
    """কানেকশন আউট হলে প্রক্সির স্ট্যাটাস live থেকে dead করা হয়"""
    try:
        supabase.table("proxies").update({"status": "dead"}).eq(
            "ip", proxy_ip
        ).execute()
    except Exception:
        pass


def call_yt_engine(url, proxy):
    """Render 502 Timeout প্রতিরোধে নিরাপদ yt_dlp ইঞ্জিন"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "proxy": proxy,
        "socket_timeout": 8,  # টাইমআউট কমাবো যাতে রিকুয়েস্ট দ্রুত রেসপন্স করে
        "nocheckcertificate": True,
        "format": "best",
        "noplaylist": True,
        "extract_flat": False,
        "ignoreerrors": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Safe extraction to prevent process crash
            info = ydl.extract_info(url, download=False)
            if info:
                # Direct URL fallback
                playback_url = info.get("url")
                if not playback_url and "formats" in info:
                    for f in info["formats"]:
                        if f.get("url"):
                            playback_url = f["url"]
                            break

                if playback_url:
                    return {
                        "success": True,
                        "playback": playback_url,
                        "title": info.get("title", "Video"),
                    }
    except Exception as e:
        err = str(e).lower()
        if any(
            msg in err
            for msg in [
                "proxy",
                "10061",
                "refused",
                "timeout",
                "failed",
                "aborted",
                "established",
                "connection",
            ]
        ):
            mark_as_dead(proxy)

    return {"success": False}


@app.route("/")
def health_check():
    return "Universal YT-Engine (Supabase Engine) is Active."


@app.route("/get-link")
def get_link():
    key = request.args.get("key")
    url = request.args.get("url")

    if key != API_KEY:
        return jsonify({"success": False, "error": "Invalid API Key"}), 401
    if not url:
        return jsonify({"success": False, "error": "URL is missing"}), 400

    try:
        # Live Proxies Fetching
        response = (
            supabase.table("proxies")
            .select("ip")
            .eq("status", "live")
            .execute()
        )
        proxy_records = response.data if response else []
    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": f"Database Error: {str(e)}"}
            ),
            500,
        )

    if not proxy_records:
        return (
            jsonify({"success": False, "error": "No Live Proxies Available"}),
            503,
        )

    proxy_list = [p["ip"] for p in proxy_records if "ip" in p]
    random.shuffle(proxy_list)

    # Render RAM সেভ করতে max_workers=3 রাখা হলো (RAM Overflow প্রতিরোধে)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(call_yt_engine, url, p): p
            for p in proxy_list[:3]
        }

        for future in as_completed(futures):
            try:
                result = future.result()
                if result and result.get("success"):
                    return jsonify(result)
            except Exception:
                continue

    return (
        jsonify(
            {
                "success": False,
                "error": "Connection Out or Proxies Failed to Extract Link",
            }
        ),
        500,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
