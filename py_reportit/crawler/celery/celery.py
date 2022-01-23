from celery import Celery
from string import Template

def create_celery_app(config: dict) -> Celery:
    broker = Template(config.get("CELERY_BROKER")).substitute({
        "CELERY_SCHEME": config.get("CELERY_SCHEME"),
        "CELERY_USER": config.get("CELERY_USER"),
        "CELERY_PASS": config.get("CELERY_PASS"),
        "CELERY_HOST": config.get("CELERY_HOST"),
        "CELERY_PORT": config.get("CELERY_PORT"),
        "CELERY_VHOST": config.get("CELERY_VHOST"),
    })

    return Celery(
        broker=broker,
        task_serializer="yaml",
        result_serializer="yaml",
        event_serialzer="yaml",
        accept_content = ["json", "yaml"],
    )
