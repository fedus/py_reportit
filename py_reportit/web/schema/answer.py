from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel

class Answer(BaseModel):
    created_at: datetime
    author: str
    text: Optional[str]
    closing: bool

    class Config:
        orm_mode = True
