# app/tasks/celery_worker.py
from celery import Celery

celery_app = Celery(
    "transcription_tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["app.tasks.transcription_tasks"]
)

celery_app.conf.task_routes = {
    "app.tasks.transcription_tasks.*": {"queue": "transcriptions"}
}
