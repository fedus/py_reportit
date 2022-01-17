from __future__ import annotations
from typing import Optional
from celery import Celery

from py_reportit.shared.config import container

from py_reportit import crawler

def create_celery_app(container: Optional[container.Container] = None) -> Celery:
    #container.wire(modules=[".tasks"])
    print(crawler.container)

    app = Celery('tasks', broker='amqp://localhost//')
    #app.container = container
    return app

app = create_celery_app()
