from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import random
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# ======================
# CONFIG & FIREBASE
# ======================
API_KEY = os.environ.get("API_KEY", "YT_SECURE_API_V1_2026_PRO")

# Environment Variable থেকে Credentials নেওয়া, না থাকলে Hardcoded fallback
FIREBASE_ENV_CRED = os.environ.get("FIREBASE_CREDENTIALS")

if FIREBASE_ENV_CRED:
    cred_dict = json.loads(FIREBASE_ENV_CRED)
    cred = credentials.Certificate(cred_dict)
else:
    firebase_credentials = {
        "type": "service_account",
        "project_id": "proxy-service-61a43",
        "private_key_id": "66ff3630a06adf5eb4eb0c11b879b53bb575794b",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCyRVuQfDvfxIHf\nrgD1RaYyluZmJWdDxHxUCitHt487GenZwVQwpYLOWQHsVSFUf1Rgu+GVBtZzXHdr\n/OWz+IhZvFwp/krgH+f2c+K9uO6SsPTf8rCKyRFXyZL2XGFPoV8MRHkqu8eblOxI\n8Fw6t0etH9e7uZj4GYvwefIm+miFJ6w8G9IRwyxf/AEUI0Sc1llxuptATY1+yItF\nKo7rxQTFvKjWCbaNCNgCAYp+0WbhZq9luhs9F8W01W/N0JSEBe0aWy7hD2nho/E0\nZUdDWyh8LqvXeazh+6TiGOmzaiqLU9hrrM+Fk3Mwq6F/fTnEKL36QpaQR24R0dC2\nzu5HXUllAgMBAAECggEAH0Ettn0xeh/XrUGyhU36v2/ZYRs5qZXvPkSyJda20+PN\nLhJJEmZSMp9ESQz71Pal8ne+KwSR4JPblCE4nH78WM8/UVV2BylQ39KddCnSGgHQ\nTNsdvJdX5Q5AJ9U2cmGWam4u2CEn88z+SCNr6BduB5pHlnAJs6W29ShMHi1U2dM5\nbny9VeothqAffo1kd5oOfOGCZDMR2DDfKCPYzjUY5fc9LfZxs9bcqz1H26kCpckf\n9T54KdgCBwJ8Gtutcmm7th7L02yI4QCoLukj/16e9+//80oKnuYt4/fzstb27EUR\nU/JCQNumjZ6n7jxHu7oNJSoggQD7m1Dwc3tjGa5SgQKBgQDusYKx5iK8etixKUxu\nJ2jmWSDMJGA/P7N4VaS2eOViQ3NsUK5/YsIa6IAe0IinFgiaXjX6lpLbseS9z39m\n62lLgYA3ygcBTzdY3OwfeU/bP78BdRP6vMiJFizai5zpOYrSxeTFhWTbSjocOHmW\nqMh5jGPL3g/ssMLtLMKkHt5nEQKBgQC/MlHsBSMlPQTf6/pf0QhAL+fwlJvZHQWr\nqpwmNJ/u6A8mCSFLWEALFAaWZLIJ7OHPBEDxiwWEv1Sen88k0NIlRs7j9/dVxxrj\nqJaiXR/hkMSC4ANxJ7jFvznTHWeHYrfrd83fPgi65XsRCzWXE1C9prN8gwnoCjKW\nQxEW2GOFFQKBgBaT1c/r+8cmO47uYBtfQO3g6lhE7JGu/dPZDf5wiwnzZVyOeSL1\nfXS8HzpK8VIUpHWtiZ+NVJDRT9igYuWiSNBqjG06f9Ug4BRYuUD04ZfUfMWvhFdI\nOhO1dEKryAjLd5UeQNhqGLMhX0PCF8YnaucMX3guJgV2Zsm2XSbXAKRxAoGBAKIT\nQvTDKhbQEgjLnjOJG+hlc8UyBKbYfk0WVEXiyEyaNPU2Oh4HkkqR0D++3lmhj42Q\neokHI0dzdYT9zXfU+L8Wthzzv5vcK0QfTooWTQdGU/7pbKGIXY5r2tXGkFNo8KXP\nqhn7GSVtkJRTHzuQ6RnLbU04O7aSpm1QLvVhu4M9AoGAQkwfc8tcMEmUFK5cKI/t\nBgcIPhqNbj2LTD4952ZutxV1FQJiOLnZLVX4OE3Cb3dU7HZC7OZFuGHTWAZGOJOD\n1DLj34aGmGNpBmK2fb/UI2ElIs3t/IIvszXKMsfsJrf/virgcfafCaLO7brZ+3mJ\nqYHZfPiTsbbYX+8TiyUx52E=\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk-fbsvc@proxy-service-61a43.iam.gserviceaccount.com",
        "client_id": "109257419616440087075",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40proxy-service-61a43.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com",
    }
    cred = credentials.Certificate(firebase_credentials)

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": "https://proxy-service-61a43-default-rtdb.firebaseio.com/"
        },
    )

LIVE_REF = db.reference("proxies/live")
DEAD_REF = db.reference("proxies/dead")


# ======================
# POWER LOGIC
# ======================


def mark_as_dead(proxy):
    try:
        data = LIVE_REF.get()
        if data:
            current_live = (
                list(data.values()) if isinstance(data, dict) else data
            )
            if proxy in current_live:
                current_live.remove(proxy)
                LIVE_REF.set(current_live)
                DEAD_REF.push(proxy)
    except Exception:
        pass


def call_yt_engine(url, proxy):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "proxy": proxy,
        "socket_timeout": 8,  # Render-এর রেসপন্স ফাস্ট রাখতে ৮ সেকেন্ড দেওয়া ভালো
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
                    "used_proxy": proxy,
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
            ]
        ):
            mark_as_dead(proxy)
    return {"success": False}


# ======================
# ROUTES
# ======================


@app.route("/")
def health_check():
    return "Universal YT-Engine V16 is Active on Render."


@app.route("/get-link")
def get_link():
    key = request.args.get("key")
    url = request.args.get("url")

    if key != API_KEY:
        return jsonify({"success": False, "error": "Invalid API Key"}), 401
    if not url:
        return jsonify({"success": False, "error": "URL is missing"}), 400

    proxies_data = LIVE_REF.get()
    if not proxies_data:
        return (
            jsonify({"success": False, "error": "No Live Proxies Available"}),
            503,
        )

    proxy_list = (
        list(proxies_data.values())
        if isinstance(proxies_data, dict)
        else proxies_data
    )
    random.shuffle(proxy_list)

    # রেস কন্ডিশন মেথড: ৫টি প্রক্সি একসাথে প্যারালাল চেক করবে
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(call_yt_engine, url, p): p for p in proxy_list[:5]
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
    app.run(host="0.0.0.0", port=port)
