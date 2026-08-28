from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/extract")
def extract_video_info(url: str = Query(..., description="Video URL")):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        # ইউটিউবের ব্লকিং বাইপাস করতে Android Client ও Player Clients ইমুলেট করা
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
        # ডিরেক্ট স্ট্রিম প্লেব্যাকের জন্য ফরম্যাট ফলব্যাক
        'format': 'best[ext=mp4]/b/best',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            direct_media_url = info.get('url')
            
            if not direct_media_url:
                raise HTTPException(status_code=404, detail="Direct playback URL not found")

            return {
                "success": True,
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "raw_playback_url": direct_media_url,
                "ext": info.get("ext"),
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
