from typing import Optional

from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, String, Unicode, UnicodeText, Numeric, DateTime, SmallInteger, Boolean, select

from py_reportit.shared.model.orm_base import Base
from py_reportit.shared.model.report_answer import ReportAnswer

class Report(Base):

    __tablename__ = 'report'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode(255))
    description = Column(UnicodeText)
    has_photo = Column(Boolean)
    latitude = Column(Numeric(8,6))
    longitude = Column(Numeric(9,6))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    key_category = Column(String(100))
    id_service = Column(SmallInteger)
    status = Column(Unicode(50))
    answers = relationship("ReportAnswer", uselist=True, backref="report")
    meta = relationship("Meta", uselist=False, backref="report")

    @hybrid_property
    def service(self) -> Optional[str]:
        if len(self.answers):
            return sorted(self.answers, key=lambda answer: answer.order)[-1].author

        return None

    @service.expression
    def service(cls):
        return select(ReportAnswer.author).where(ReportAnswer.report_id == cls.id).order_by(ReportAnswer.order.desc()).limit(1).as_scalar()

    def __repr__(self):
        return f'<Report-It id={self.id!r}\n\
            title={self.title}\n\
            description={self.description}\n\
            has_photo={self.has_photo}\n\
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
