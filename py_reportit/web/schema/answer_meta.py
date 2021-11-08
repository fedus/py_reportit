from pydantic import BaseModel

class AnswerMeta(BaseModel):
    language: str

    class Config:
        orm_mode = True
