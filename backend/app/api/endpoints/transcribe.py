from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.modules.stt.transcriber import GroqTranscriber
from app.modules.stt.post_processor import TranscriptPostProcessor

router = APIRouter()
transcriber = GroqTranscriber()
post_processor = TranscriptPostProcessor()

class TranscribeResponse(BaseModel):
    transcript: str
    raw_transcript: str

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    try:
        raw = await transcriber.transcribe(audio_bytes, file.filename)
        cleaned = post_processor.process(raw)
        return TranscribeResponse(transcript=cleaned, raw_transcript=raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
