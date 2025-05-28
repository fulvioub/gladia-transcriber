from flask import Flask, request, jsonify
import requests
import time
import openai
import os

app = Flask(__name__)

GLADIA_KEY = os.getenv("GLADIA_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    data = request.json
    youtube_url = data.get("youtube_url")
    if not youtube_url:
        return jsonify({"error": "Missing YouTube URL"}), 400

    # Step 1: Request transcription
    response = requests.post(
        "https://api.gladia.io/audio/text/audio-transcription/",
        headers={
            "x-gladia-key": GLADIA_KEY,
            "Content-Type": "application/json"
        },
        json={
            "audio_url": youtube_url,
            "language": "en",
            "youtube_dl": True,
            "toggle_noise_reduction": False,
            "toggle_diarization": False,
            "toggle_direct_translate": False
        }
    )
    if response.status_code != 200:
        return jsonify({"error": "Failed to submit to Gladia", "details": response.json()}), 500

    transcript_id = response.json().get("transcription_id")
    if not transcript_id:
        return jsonify({"error": "No transcription_id returned"}), 500

    # Step 2: Poll Gladia
    for _ in range(20):
        time.sleep(10)
        poll = requests.get(
            f"https://api.gladia.io/audio/text/audio-transcription/{transcript_id}",
            headers={"x-gladia-key": GLADIA_KEY}
        )
        result = poll.json()
        if result.get("status") == "done":
            transcription = result.get("prediction", "")
            break
    else:
        return jsonify({"error": "Gladia timeout"}), 504

    # Step 3: Send to OpenAI for blog
    openai.api_key = OPENAI_KEY
    prompt = f"Write a blog post based on this transcript:\n\n{transcription}"
    completion = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a medical copywriter."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    blog = completion.choices[0].message.content
    return jsonify({"blog": blog})