import redis
import os
import json 

class EventChannelManager:
    def __init__(self):
        self.redis_client = redis.StrictRedis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=6379,
            db=0,
            decode_responses=True
        )
        self.pubsubs = {}

    def send_to_channel(self, task_id: str, message: str):
        """Publica un mensaje en el canal de Redis"""
        self.redis_client.publish(task_id, message)

    def listen_to_channel(self, task_id: str):
        """Escucha un canal en Redis"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(task_id)
        self.pubsubs[task_id] = pubsub
        return pubsub

    def delete_channel(self, task_id: str):
        """Elimina la suscripción a un canal de Redis"""
        pubsub = self.pubsubs.pop(task_id, None)
        if pubsub:
            pubsub.unsubscribe(task_id)
            pubsub.close()
            print(f"🔚 Canal {task_id} cerrado correctamente en Redis")
        else:
            print(f"⚠️ No se encontró una suscripción activa para el canal {task_id}")

    def get_cached_message(self, task_id: str):
        """Obtiene un mensaje cacheado si existe"""
        cached_message = self.redis_client.get(f"cached_{task_id}")
        if cached_message:
            print(f"💡 Mensaje encontrado en caché para {task_id}: {cached_message}")
        else:
            print(f"❌ No se encontró caché para {task_id}")
        return cached_message

    def cache_result(self, task_id: str, data: dict, ttl: int = 300):
        """Guarda el resultado procesado en la caché de Redis por un tiempo limitado (TTL)."""
        self.redis_client.set(f"cached_{task_id}", json.dumps(data), ex=ttl)
        print(f"🧠 Resultado cacheado para {task_id} por {ttl} segundos")