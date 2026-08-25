from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import random
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

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ======================
# POWER LOGIC
# ======================


def mark_as_dead(proxy_ip):
    """কানেকশন আউট বা ব্যান্ডউইথ শেষ হলে প্রক্সির স্ট্যাটাস live থেকে dead করে দেওয়া হয়"""
    try:
        supabase.table("proxies").update({"status": "dead"}).eq(
            "ip", proxy_ip
        ).execute()
    except Exception:
        pass


def call_yt_engine(url, proxy):
    """প্রতিটি প্রক্সির জন্য আলাদা থ্রেড ইঞ্জিন"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "proxy": proxy,
        "socket_timeout": 12,  # স্লো প্রক্সির জন্য ১২ সেকেন্ড বাফার
        "nocheckcertificate": True,
        "format": "best",
        "noplaylist": True,
        "extract_flat": False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            original_url = info.get("url")
            if original_url:
                return {
                    "success": True,
                    "playback": original_url,
                    "title": info.get("title"),
                }
    except Exception as e:
        err = str(e).lower()
        # Connection Out এর সব কন্ডিশন
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
            ]
        ):
            mark_as_dead(proxy)
    return {"success": False}


# ======================
# HIGH-CONCURRENCY ROUTES
# ======================


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

    # Supabase থেকে কেবল 'live' স্ট্যাটাসের প্রক্সিগুলো সংগ্রহ করা
    try:
        response = (
            supabase.table("proxies")
            .select("ip")
            .eq("status", "live")
            .execute()
        )
        proxy_records = response.data
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

    # রেস কন্ডিশন মেথড: ৫টি প্রক্সি একসাথে কাজ শুরু করবে
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(call_yt_engine, url, p): p
            for p in proxy_list[:5]
        }

        for future in as_completed(futures):
            result = future.result()
            if result.get("success"):
                return jsonify(result)

    return (
        jsonify(
            {"success": False, "error": "Connection Out or Proxy Limit Reached"}
        ),
        500,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
