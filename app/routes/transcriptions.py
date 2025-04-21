from fastapi import APIRouter, HTTPException, Depends, Query
from app.core.database import users_collection
from app.core.auth import get_current_user
from app.schemas.transcription_schema import Transcription, TranscriptionInput
from app.models.emotion_model import predict_emotion
from app.models.sentiment_model import predict_sentiment
from app.models.transcribe_model import transcribe_audio_from_file
from datetime import datetime, date, time
from fastapi import APIRouter, UploadFile, File

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

    # Llamar al modelo de transcripción
    try:
        text = transcribe_audio_from_file(file_bytes, suffix=f".{audio.filename.split('.')[-1]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    # Predecir emoción y sentimiento usando el texto
    emotion_data = predict_emotion(text)
    emotion = emotion_data["predicted_emotion"]
    emotion_probs = emotion_data["probabilities"]

    sentiment, sentiment_probs = predict_sentiment(text)

    # Construir la transcripción con fecha y hora actuales
    transcription_data = {
        "_id": str(ObjectId()),
        "date": datetime.now().date().isoformat(),
        "time": datetime.now().time().isoformat(timespec="seconds"),
        "text": text,
        "emotion": emotion,
        "emotionProbabilities": emotion_probs,
        "sentiment": sentiment,
        "sentimentProbabilities": sentiment_probs,
        "topic": None
    }

    # Insertar en la colección del usuario
    result = await users_collection.update_one(
        {"_id": user_id},
        {"$push": {"transcriptions": transcription_data}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to add transcription")

    return {
        "message": "Transcription added successfully",
        "transcription_id": transcription_data["_id"]
    }

@router.post("/add-transcription/text")
async def add_transcription_auto(
    input: TranscriptionInput,
    user_id: str = Depends(get_current_user)
):
    # Extraer el texto desde el cuerpo
    text = input.text

    # Verificar si el usuario existe
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Predecir emoción y sentimiento
    emotion_data = predict_emotion(text)
    emotion = emotion_data["predicted_emotion"]
    emotion_probs = emotion_data["probabilities"]
    
    sentiment, sentiment_probs = predict_sentiment(text)

    # Armar el objeto de transcripción
    transcription_data = {
        "_id": str(ObjectId()),
        "date": datetime.now().date().isoformat(),
        "time": datetime.now().time().isoformat(timespec="seconds"),
        "text": text,
        "emotion": emotion,
        "emotionProbabilities": emotion_probs,
        "sentiment": sentiment,
        "sentimentProbabilities": sentiment_probs,
        "topic": None  
    }

    # Guardar la transcripción
    result = await users_collection.update_one(
        {"_id": user_id},
        {"$push": {"transcriptions": transcription_data}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to add transcription")

    return {
        "message": "Transcription added successfully",
        "transcription_id": transcription_data["_id"]
    }