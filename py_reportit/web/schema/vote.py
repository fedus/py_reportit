from pydantic import BaseModel
from uuid import UUID

class Vote(BaseModel):
    category_id: int

    class Config:
        orm_mode = True

