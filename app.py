import os
import tempfile
import requests
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

GLADIA_API_KEY = os.environ.get("GLADIA_API_KEY")

@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.get_json()
    youtube_url = data.get('youtube_url')
    if not youtube_url:
        return jsonify({"error": "Missing YouTube URL"}), 400

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': tmp_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        with open(tmp_path, 'rb') as f:
            files = {'audio': ('audio.mp3', f, 'audio/mpeg')}
            headers = {
                'x-gladia-key': GLADIA_API_KEY,
            }
            response = requests.post(
                'https://api.gladia.io/audio/text/audio-transcription/',
                headers=headers,
                files=files
            )
            result = response.json()
        
        os.remove(tmp_path)
        return jsonify(result), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500
