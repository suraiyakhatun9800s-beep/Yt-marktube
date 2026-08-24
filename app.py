from datetime import datetime
from fastapi import FastAPI, HTTPException
import requests
import yt_dlp

app = FastAPI()


def get_archive_proxy():
    date_str = datetime.now().strftime("%Y-%m-%d")
    api_url = f"https://api.checkerproxy.net/v1/landing/archive/{date_str}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        res = requests.get(api_url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json().get("data", {}).get("proxyList", [])
    except Exception:
        pass
    return []


def test_proxy(proxy_str):
    """প্রক্সি লাইভ এবং কাজ করছে কিনা ইউটিউব এন্ডপয়েন্টে ৩ সেকেন্ডে টেস্ট করবে"""
    test_url = "https://www.youtube.com/generate_204"
    proxy_dict = {"http": f"http://{proxy_str}", "https": f"http://{proxy_str}"}

    try:
        # ৩ সেকেন্ডের কানেকশন টাইমআউট
        res = requests.get(test_url, proxies=proxy_dict, timeout=3)
        if res.status_code in [200, 204]:
            return True
    except Exception:
        return False
    return False


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Proxy Validator & Direct Stream URL Extractor is Live!",
    }


@app.get("/extract")
def extract_direct_url(url: str):
    proxies = get_archive_proxy()
    working_proxy = None

    # ১. দ্রুত প্রক্সি ভ্যালিডেশন লুপ (প্রথম ২০টি টেস্ট করবে)
    for proxy in proxies[:20]:
        if test_proxy(proxy):
            working_proxy = proxy
            break  # প্রথম অ্যাক্টিভ প্রক্সিটি পেয়ে গেলেই টেস্ট বন্ধ করবে

    # ২. যদি কোনো অ্যাক্টিভ প্রক্সি পাওয়া যায়, সেটি দিয়ে yt-dlp রান করবে
    if working_proxy:
        proxy_addr = f"http://{working_proxy}"
        ydl_opts = {
            "format": "best",
            "proxy": proxy_addr,
            "quiet": True,
            "skip_download": True,
            "socket_timeout": 8,
            "nocheckcertificate": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and "url" in info:
                    return {
                        "status": "success",
                        "title": info.get("title"),
                        "direct_url": info.get("url"),
                        "used_proxy": working_proxy,
                    }
        except Exception:
            pass  # ভ্যালিডেশন করা প্রক্সি মাঝপথে কোনো কারণে ড্রপ করলে fallback-এ যাবে

    # ৩. অ্যাক্টিভ প্রক্সি না পাওয়া গেলে বা ব্যর্থ হলে Direct Connection চেষ্টা করবে
    try:
        ydl_opts = {
            "format": "best",
            "quiet": True,
            "skip_download": True,
            "nocheckcertificate": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "status": "success",
                "title": info.get("title"),
                "direct_url": info.get("url"),
                "used_proxy": "Direct Connection (No Active Public Proxy Found)",
            }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Extraction failed: {str(e)}"
        )
