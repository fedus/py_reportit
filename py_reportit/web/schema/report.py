from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel

from py_reportit.web.schema.answer import Answer

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
    answers: List[Answer] = []

    class Config:
        orm_mode = True
