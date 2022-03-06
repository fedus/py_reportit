from datetime import datetime
from typing import Optional
from uuid import UUID
from arrow import Arrow

from pydantic import BaseModel, validator


class User(BaseModel):
    id: UUID
    username: str
    created_at: datetime
    last_login: Optional[datetime]
    admin: bool
    disabled: bool

    class Config:
        orm_mode = True

    @validator("created_at", "last_login", pre=True)
    def format_datetime(cls, value: Optional[Arrow]):
        if value:
            return value._datetime
