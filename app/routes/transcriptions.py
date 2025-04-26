from fastapi import APIRouter, HTTPException, Depends, Query
from app.core.database import users_collection
from app.core.auth import get_current_user
from app.schemas.transcription_schema import Transcription, TranscriptionInput
from app.tasks.transcription_tasks import process_audio_transcription, process_text_transcription
from datetime import datetime, date, time
from fastapi import APIRouter, UploadFile, File
import base64
from typing import Optional
from bson import ObjectId

router = APIRouter()

@router.post("/add-transcription/audio")
async def add_transcription_audio(
    audio: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    # Verificar si el usuario existe
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Leer el contenido del archivo
    file_bytes = await audio.read()
    file_bytes_b64 = base64.b64encode(file_bytes).decode('utf-8')

    # Llamar a la tarea de Celery para procesar la transcripción
    result = process_audio_transcription.apply_async(
        (user_id, file_bytes_b64, f".{audio.filename.split('.')[-1]}"),
        queue="transcriptions"
    )

    return {
        "message": "Transcription enqueued successfully",
        "task_id": result.id
    }

@router.post("/add-transcription/text")
async def add_transcription_text(
    input: TranscriptionInput,
    user_id: str = Depends(get_current_user)
):
    # Verificar si el usuario existe
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Encolar tarea de Celery
    result = process_text_transcription.apply_async(
        (user_id, input.text),
        queue="transcriptions"
    )

    return {
        "message": "Transcription enqueued successfully",
        "task_id": result.id
    }