from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from py_reportit.web.schema.answer_meta import AnswerMeta

class Answer(BaseModel):
    created_at: datetime
    author: str
    text: Optional[str]
    closing: bool
    meta: AnswerMeta

    class Config:
        orm_mode = True
