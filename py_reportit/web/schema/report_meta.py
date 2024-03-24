from typing import Optional
from pydantic import BaseModel

from py_reportit.web.schema.category import Category

class ReportMeta(BaseModel):
    language: str
    address_street: Optional[str]
    address_neighbourhood: Optional[str]
    address_postcode: Optional[int]
    category: Optional[Category]

    class Config:
        from_attributes = True
