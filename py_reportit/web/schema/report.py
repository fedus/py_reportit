from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel

from py_reportit.web.schema.answer import Answer
from py_reportit.web.schema.meta import Meta

class Report(BaseModel):
    id: int
    title: Optional[str]
    description: Optional[str]
    photo_url: Optional[str]
    thumbnail_url: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime
    updated_at: datetime
    key_category: Optional[str]
    id_service: Optional[int]
    status: str
    meta: Meta
    answers: List[Answer] = []

    class Config:
        orm_mode = True

class PagedReportList(BaseModel):
    previous: Optional[str]
    next: Optional[str]
    total_count: int
    reports: list[Report]
