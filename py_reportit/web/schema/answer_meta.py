from pydantic import BaseModel

class AnswerMeta(BaseModel):
    language: str

    class Config:
        from_attributes = True
