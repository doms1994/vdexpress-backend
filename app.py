from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from yt_dlp import YoutubeDL
import os
import uuid

app = Flask(__name__)
CORS(app, origins=["https://domcreator.co.uk"])

DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def detect_platform(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "instagram.com" in url:
        return "Instagram"
    elif "facebook.com" in url or "fb.watch" in url:
        return "Facebook"
    elif "twitter.com" in url or "x.com" in url:
        return "Twitter"
    else:
        return "Unknown"

@app.route("/fetch-thumbnail", methods=["POST"])
def fetch_thumbnail():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    if detect_platform(url) == "YouTube":
        return jsonify({"error": "YouTube videos are not currently supported. Try Instagram, Facebook, or Twitter."})

    try:
        ydl_opts = {
            'quiet': True,
            'noplaylist': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "thumbnail": info.get("thumbnail"),
                "platform": detect_platform(url),
                "title": info.get("title", "Video")
            })
    except Exception as e:
        err = str(e)
        if '302' in err or 'redirect' in err:
            return jsonify({"error": "This video link is redirecting too many times. Try using a full desktop post URL instead."})
        return jsonify({"error": err}), 500

@app.route("/download", methods=["POST"])
def download():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    if detect_platform(url) == "YouTube":
        return jsonify({"error": "YouTube videos are not currently supported. Try Instagram, Facebook, or Twitter."})

    try:
        filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join(DOWNLOAD_FOLDER, filename)

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'noplaylist': True
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return jsonify({ "download_url": f"/downloaded/{filename}" })

    except Exception as e:
        err = str(e)
        if '302' in err or 'redirect' in err:
            return jsonify({"error": "This video link is redirecting too many times. Try using a full desktop post URL instead."})
        return jsonify({"error": err}), 500

@app.route("/downloaded/<filename>")
def serve_video(filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return abort(404)

    try:
        return send_file(filepath, as_attachment=True)
    finally:
        try:
            os.remove(filepath)
        except:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
