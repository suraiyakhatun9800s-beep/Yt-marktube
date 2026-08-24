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


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Direct Stream URL Extractor is running!",
    }


@app.get("/extract")
def extract_direct_url(url: str):
    proxies = get_archive_proxy()

    # ১. প্রথমে Checkerproxy Archive-এর প্রথম ১০টি প্রক্সি চেক করবে
    for proxy in proxies[:10]:
        proxy_addr = f"http://{proxy}"
        ydl_opts = {
            "format": "best",
            "proxy": proxy_addr,
            "quiet": True,
            "skip_download": True,
            "socket_timeout": 5,
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
                        "used_proxy": proxy,
                    }
        except Exception:
            continue

    # ২. প্রক্সিগুলো কাজ না করলে সরাসরি (Direct Connection) চেষ্টা করবে
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
                "used_proxy": "Direct Connection (No Proxy)",
            }
    except Exception as e:
        # ৫০০ এরর না দিয়ে আসল এরর মেসেজ দেখাবে
        raise HTTPException(
            status_code=400, detail=f"yt-dlp Extraction Error: {str(e)}"
        )
