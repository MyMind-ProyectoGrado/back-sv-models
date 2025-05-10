from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from app.core.database import users_collection
from app.core.auth import get_current_user
from app.core.event_channel_manager import EventChannelManager
from app.schemas.transcription_schema import Transcription, TranscriptionInput
from app.tasks.transcription_tasks import process_audio_transcription, process_text_transcription
import base64
from typing import Optional
from bson import ObjectId
import asyncio
import time
import json
from fastapi.responses import StreamingResponse
from app.schemas.transcription_schema import Transcription
router = APIRouter()

# Manejador de eventos
event_manager = EventChannelManager()

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

    task_id = result.id
    print(f"🔔 Task encolada exitosamente con ID: {task_id}")

    # Inicializar el canal aquí para que esté activo desde ya
    event_manager.listen_to_channel(task_id)

    return {
        "message": "Transcription enqueued successfully",
        "task_id": task_id
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

    task_id = result.id
    print(f"🔔 Task encolada exitosamente con ID: {task_id}")

    # Inicializar el canal aquí para que esté activo desde ya
    event_manager.listen_to_channel(task_id)

    return {
        "message": "Transcription enqueued successfully",
        "task_id":  task_id
    }


@router.get("/stream/{task_id}")
async def get_result(task_id: str, timeout: int = 60):
    """
    Espera el resultado publicado en Redis para el task_id dado.
    Si no se recibe nada en 'timeout' segundos, se cierra el canal y retorna error.
    """
    # Revisión de caché (si ya se tiene resultado previo)
    cached = event_manager.get_cached_message(task_id)
    if cached is not None:
        try:
            cached_data = json.loads(cached)
            transcription = Transcription(**cached_data)
            # ❌ Borrar el caché después de devolverlo
            event_manager.redis_client.delete(f"cached_{task_id}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing cached result: {str(e)}")

        return {
            "task_id": task_id,
            "result": transcription.dict(),
            "cached": True
        }

    # Suscripción al canal Redis (pubsub)
    pubsub = event_manager.listen_to_channel(task_id)
    start_time = time.time()

    try:
        while time.time() - start_time < timeout:
            message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

            if message and message['type'] == 'message':
                result = message['data']

                try:
                    result_data = json.loads(result)
                    transcription = Transcription(**result_data)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error parsing result into schema: {str(e)}")

                # Guardar en caché por 5 minutos
                event_manager.redis_client.setex(f"cached_{task_id}", 300, result)

                return {
                    "task_id": task_id,
                    "result": transcription.dict(),
                    "cached": False
                }

            await asyncio.sleep(0.5)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resultado: {str(e)}")

    finally:
        # Cerrar suscripción al canal
        event_manager.delete_channel(task_id)

    # Timeout sin resultado
    raise HTTPException(
        status_code=408,
        detail=f"No se recibió respuesta para task_id '{task_id}' en {timeout} segundos."
    )