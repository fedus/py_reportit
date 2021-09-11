from py_reportit.shared.model.orm_base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Unicode, UnicodeText, Numeric, DateTime, SmallInteger

class Report(Base):

    __tablename__ = 'report'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255))
    description = Column(UnicodeText)
    photo_url = Column(String(100))
    thumbnail_url = Column(String(100))
    latitude = Column(Numeric(8,6))
    longitude = Column(Numeric(9,6))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    key_category = Column(String(100))
    id_service = Column(SmallInteger)
    status = Column(Unicode(50))
    answers = relationship("ReportAnswer", uselist=True)
    meta = relationship("Meta", uselist=False)

    def __repr__(self):
        return f'<Report-It id={self.id!r}\n\
            title={self.title}\n\
            description={self.description}\n\
            photo_url={self.photo_url}\n\
            thumbnail_url={self.thumbnail_url}\n\
            latitude={self.latitude}\n\
            longitude={self.longitude}\n\
            created_at={self.created_at}\n\
            updated_at={self.updated_at}\n\
            key_category={self.key_category}\n\
            id_service={self.id_service}\n\
            status={self.status}\n\
            answers={self.answers}\n\
            meta={self.meta}>'

    @property
    def has_title(self):
        return self.title != None and self.title != "" and self.title != "title"
