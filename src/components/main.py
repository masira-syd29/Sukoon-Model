# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fastapi.responses import JSONResponse
import json
from fastapi import UploadFile, File
import whisper
import base64
import soundfile as sf
import io
import torch

# Load environment variables
load_dotenv()
print("API KEY LOADED:", os.getenv("GEMINI_API_KEY") is not None)

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# FastAPI app setup
app = FastAPI(
    title="Sukoon Backend",
    description="Mental health assistant powered by Gemini & AI",
    version="0.1"
)

# Allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Change to ["http://localhost:3000"] for stricter security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add ffmpeg path to PATH just for this script
os.environ["PATH"] += os.pathsep + r"C:\Users\Madiha\Downloads\ffmpeg-master-latest-win64-gpl-shared\ffmpeg-master-latest-win64-gpl-shared\bin"

# Load Whisper model once at startup (not every request → faster)
whisper_model = whisper.load_model("base")

# Example: Using Coqui TTS model (adjust if you're using another one)
from TTS.api import TTS  
tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")  # example model

# Request/Response Models
class SpeechInput(BaseModel):
    audio_data: str  # base64 encoded audio

class TextInput(BaseModel):
    text: str
    system_instruction: str
    emotion: str

class GeminiRequest(BaseModel):
    system_instruction: str
    contents: str
    emotions: dict | None = None

class EmotionResponse(BaseModel):
    emotion: str
    # suggestions: Optional[List[str]] = []

# 1️⃣ Health Check
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Sukoon backend running"}

# 2️⃣ Speech-to-Text Endpoint
@app.post("/stt")
async def convert_speech_to_text(audio: UploadFile = File(...)):
    try:
        file_location = f"temp_{audio.filename}"
        with open(file_location, "wb") as f:
            f.write(await audio.read())

        result = whisper_model.transcribe(file_location)
        os.remove(file_location)
        print(result)

        return {"text": result["text"]}
    except Exception as e:
        return {"error": str(e)}

# 3️⃣ Emotion Detection Endpoint
@app.post("/emotion_detection", response_model=EmotionResponse)
def detect_emotion(req: TextInput):
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=req.text,
        config=types.GenerateContentConfig(
            system_instruction=req.system_instruction,
            temperature=0.3,
            candidate_count=1,
        ),
    )

    try:
        # Try to parse Gemini response as JSON
        result = json.loads(response.text)
        return EmotionResponse(emotion=result.get("emotion", "unknown"))

    except json.JSONDecodeError:
        # Fallback: Gemini gave plain text instead of JSON
        return EmotionResponse(
            emotion=response.text.strip() if response.text.strip() else "unknown"
        )

# 4️⃣ Text-to-Speech Endpoint
@app.post("/tts")
def convert_text_to_speech(payload: TextInput) -> Dict:
    text = payload.text

    # Always overwrite the same file
    output_path = "latest_tts.wav"

    # Generate speech and save to file
    tts.tts_to_file(text=text, file_path=output_path)

    # Read back and encode to base64
    with open(output_path, "rb") as f:
        audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return {"audio_data": audio_base64}

# 5️⃣ Gemini API Endpoint (real model call)
@app.post("/gemini")
def get_gemini_suggestions(req: GeminiRequest) -> Dict:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=req.contents,
            config=types.GenerateContentConfig(
                system_instruction=req.system_instruction,
                temperature=0.5,
                candidate_count=1
            )
        )

        if not response or not response.text:
            return JSONResponse(
                status_code=500,
                content={"error": "Gemini API returned no text."}
            )

        return {"response": response.text}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )