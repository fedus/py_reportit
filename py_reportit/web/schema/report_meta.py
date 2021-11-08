from typing import Optional
from pydantic import BaseModel

class ReportMeta(BaseModel):
    language: str
    address_street: Optional[str]
    address_neighbourhood: Optional[str]
    address_postcode: Optional[int]

    class Config:
        orm_mode = True
