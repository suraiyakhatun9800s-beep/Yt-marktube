from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI(
    title="Universal Video Extractor API",
    description="yt-dlp ব্যবহার করে ভিডিওর ডিরেক্ট স্ট্রিমিং ও প্লেব্যাক লিঙ্ক বের করার API"
)

# CORS এনাবল করা হলো যাতে যেকোনো ফ্রন্টএন্ড বা ওয়েবসাইট থেকে কল করা যায়
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "online", "message": "Video Extractor API runs successfully!"}

@app.get("/api/extract")
def extract_video_info(url: str = Query(..., description="ভিডিওর পুরো URL এখানে দিন")):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        # 'b' বা 'best' ফরম্যাট সিলেক্ট করবে যা সাধারণত অডিও ও ভিডিও একসাথে কম্বাইন্ড Direct MP4 Stream প্রদান করে
        'format': 'b/best',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # সরাসরি ড্রাইভ করা ভিডিও বা মিডিয়া স্ট্রিম লিঙ্ক
            direct_media_url = info.get('url')
            
            if not direct_media_url:
                raise HTTPException(status_code=404, detail="Direct media stream URL not found")

            return {
                "success": True,
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "raw_playback_url": direct_media_url, # এটিই আপনার কাঙ্ক্ষিত প্লেব্যাক লিংক
                "ext": info.get("ext"),
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
