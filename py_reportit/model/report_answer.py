from typing import Text

from sqlalchemy.sql.sqltypes import Unicode
from py_reportit.model.orm_base import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, DateTime, Boolean, SmallInteger, Integer, UnicodeText, ForeignKey

class ReportAnswer(Base):

    __tablename__ = 'report_answer'

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('report.id'), nullable=False)
    order = Column(SmallInteger)
    created_at = Column(DateTime)
    author = Column(Unicode(100))
    text = Column(UnicodeText)
    closing = Column(Boolean, default=False)
    meta = relationship("ReportAnswerMeta", uselist=False)

    def __repr__(self):
        repr = f'<ReportAnswer\
            id={self.id!r}\
            report_id={self.report_id!r}\
            order={self.order!r}\
            created_at={self.created_at!r}\
            author={self.author!r}\
            text={self.text!r}\
            closing={self.closing!r}>'
        return ' '.join(repr.split())