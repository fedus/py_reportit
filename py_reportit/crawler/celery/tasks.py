from __future__ import annotations

from dependency_injector.wiring import inject, Provide
from celery import shared_task
from py_reportit.crawler.service.reportit_api import ReportItService

@shared_task
@inject
def add(x, y, something: ReportItService = Provide['reportit_service']):
    print(something)
    if x < 10:
        add.delay(x+1,y+1)
    return x + y
