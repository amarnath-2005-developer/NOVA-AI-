"""
NOVA AI — Groq Whisper STT Transcriber
Sends audio to Groq's high-speed Whisper-large-v3 endpoint.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ASR_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

class GroqTranscriber:
    """
    Transcribes audio using Groq's LPU-powered Whisper-large-v3.
    """

    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.url = GROQ_ASR_URL
        self.model = "whisper-large-v3"
        self.timeout = 30.0

        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in .env")

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        # MIME type detection
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"
        mime_map = {
            "wav": "audio/wav",
            "webm": "audio/webm",
            "ogg": "audio/ogg",
            "mp3": "audio/mpeg",
        }
        mime = mime_map.get(ext, "audio/wav")

        files = {
            "file": (filename, audio_bytes, mime),
        }
        data = {
            "model": self.model,
            "language": "en",
            "response_format": "json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.url,
                headers=headers,
                files=files,
                data=data,
            )

            if response.status_code != 200:
                raise RuntimeError(f"Groq STT Error ({response.status_code}): {response.text}")

            result = response.json()
            return result.get("text", "").strip()
