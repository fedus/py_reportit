from celery import Celery

from py_reportit.crawler import container

def create_celery_app() -> Celery:
    container.wire(modules=[".tasks"])

    app = Celery('tasks', broker='amqp://localhost//')
    app.container = container
    return app

app = create_celery_app()
