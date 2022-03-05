from sqlalchemy import Column, Integer, Unicode

from py_reportit.shared.model.orm_base import Base

class Category(Base):

    __tablename__ = "category"

    id = Column(Integer, primary_key=True)
    label = Column(Unicode(100))
