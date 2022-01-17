from __future__ import annotations

from dependency_injector.wiring import inject, Provide
from py_reportit.crawler.celery.celery import app
from py_reportit.shared.config import container

@app.task
@inject
def add(x, y, bla = Provide[container.Container.geocoder_service]):
    print(bla)
    if x < 10:
        add.delay(x+1,y+1)
    return x + y
