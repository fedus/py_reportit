from pydantic import BaseModel

class Category(BaseModel):
    id: int
    label: str

    class Config:
        orm_mode = True

class CategoryPost(BaseModel):
    label: str

    class Config:
        orm_mode = True
