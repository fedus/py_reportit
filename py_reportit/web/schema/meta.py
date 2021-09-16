from pydantic import BaseModel

class Meta(BaseModel):
    language: str

    class Config:
        orm_mode = True
