from py_reportit.model.orm_base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Unicode, UnicodeText, Numeric, DateTime, SmallInteger

class Report(Base):

    __tablename__ = 'report'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255))
    description = Column(UnicodeText)
    photo_url = Column(String(100))
    thumbnail_url = Column(String(100))
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    key_category = Column(String(100))
    id_service = Column(SmallInteger)
    status = Column(Unicode(50))
    meta = relationship("Meta", uselist=False)

    def __repr__(self):
        return f'<Report-It id={self.id!r}>'

    @property
    def has_title(self):
        return self.title != None and self.title != ""
