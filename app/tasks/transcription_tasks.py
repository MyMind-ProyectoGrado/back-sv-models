# app/tasks/transcription_tasks.py
from app.tasks.celery_worker import celery_app
from app.models.transcribe_model import transcribe_audio_from_file
from app.models.emotion_model import predict_emotion
from app.models.sentiment_model import predict_sentiment
from app.core.database import users_collection
from datetime import datetime
from bson import ObjectId
from pydub import AudioSegment
import io
import base64

@celery_app.task
def process_audio_transcription(user_id: str, file_bytes_b64: str, extension: str):
    print(f"🔔 Recibido task de audio para user_id: {user_id}")
    
    file_bytes = base64.b64decode(file_bytes_b64)
    print("✅ Archivo de audio decodificado")

    clean_extension = extension.lower().lstrip(".")

    if clean_extension != "wav":
        # 🔄 Convertir a WAV solo si no está ya en WAV
        audio = AudioSegment.from_file(io.BytesIO(file_bytes), format=clean_extension)
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        print("🔊 Audio convertido a formato WAV")
        audio_bytes = wav_buffer.read()
    else:
        print("🎧 Archivo ya está en formato WAV, se omite la conversión")
        audio_bytes = file_bytes
    
    text = transcribe_audio_from_file(audio_bytes, suffix="wav")
    print(f"📝 Texto transcrito: {text[:50]}...")  # Mostrar solo los primeros 50 caracteres

    emotion_data = predict_emotion(text)
    sentiment, sentiment_probs = predict_sentiment(text)
    print(f"🎭 Emoción: {emotion_data['predicted_emotion']}, 😊 Sentimiento: {sentiment}")

    transcription_data = {
        "_id": str(ObjectId()),
        "date": datetime.now().date().isoformat(),
        "time": datetime.now().time().isoformat(timespec="seconds"),
        "text": text,
        "emotion": emotion_data["predicted_emotion"],
        "emotionProbabilities": emotion_data["probabilities"],
        "sentiment": sentiment,
        "sentimentProbabilities": sentiment_probs,
        "topic": None
    }

    users_collection.update_one(
        {"_id": user_id},
        {"$push": {"transcriptions": transcription_data}}
    )
    print(f"📦 Transcripción guardada en MongoDB para el usuario {user_id}")

@celery_app.task
def process_text_transcription(user_id: str, text: str):
    print(f"🧾 Recibido task de texto para user_id: {user_id}")
    print(f"Texto: {text[:50]}...")  # Mostrar solo parte para no saturar

    emotion_data = predict_emotion(text)
    sentiment, sentiment_probs = predict_sentiment(text)
    print(f"🎭 Emoción: {emotion_data['predicted_emotion']}, 😊 Sentimiento: {sentiment}")

    transcription_data = {
        "_id": str(ObjectId()),
        "date": datetime.now().date().isoformat(),
        "time": datetime.now().time().isoformat(timespec="seconds"),
        "text": text,
        "emotion": emotion_data["predicted_emotion"],
        "emotionProbabilities": emotion_data["probabilities"],
        "sentiment": sentiment,
        "sentimentProbabilities": sentiment_probs,
        "topic": None
    }

    users_collection.update_one(
        {"_id": user_id},
        {"$push": {"transcriptions": transcription_data}}
    )
    print(f"📦 Transcripción guardada en MongoDB para el usuario {user_id}")