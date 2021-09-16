from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from py_reportit.web.schema.meta import Meta

class Answer(BaseModel):
    created_at: datetime
    author: str
    text: Optional[str]
    closing: bool
    meta: Meta

    class Config:
        orm_mode = True
