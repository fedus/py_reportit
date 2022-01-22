from celery import Celery

def create_celery_app(broker: str) -> Celery:
    return Celery(broker=broker, task_serializer='yaml', timezone="Europe/Luxembourg")
