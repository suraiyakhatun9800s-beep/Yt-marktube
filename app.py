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
    except:
        pass
    return []


@app.get("/")
def home():
    return {
        "message": "Render Direct URL Extractor is Live!",
        "usage": "/extract?url=YOUR_VIDEO_URL",
    }


@app.get("/extract")
def extract_direct_url(url: str):
    proxies = get_archive_proxy()

    # আর্কাইভ প্রক্সিগুলো ট্রাই করবে
    for proxy in proxies[:15]:
        proxy_addr = f"http://{proxy}"
        ydl_opts = {
            "format": "best",
            "proxy": proxy_addr,
            "quiet": True,
            "skip_download": True,
            "socket_timeout": 5,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "status": "success",
                    "title": info.get("title"),
                    "direct_url": info.get("url"),
                    "used_proxy": proxy,
                }
        except Exception:
            continue

    # প্রক্সি ফেইল করলে ডাইরেক্ট ট্রাই করবে
    try:
        ydl_opts = {"format": "best", "quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "status": "success",
                "title": info.get("title"),
                "direct_url": info.get("url"),
                "used_proxy": "Direct Connection",
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to extract URL: {str(e)}"
        )
