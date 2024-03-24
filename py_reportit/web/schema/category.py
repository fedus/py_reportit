from pydantic import BaseModel

class Category(BaseModel):
    id: int
    label: str

    class Config:
        from_attributes = True

class CategoryPost(BaseModel):
    label: str

    class Config:
        from_attributes = True
