from typing import Text
from py_reportit.model.orm_base import Base
from sqlalchemy import Column, Integer, Boolean, ForeignKey, text

class Meta(Base):

    __tablename__ = 'meta'

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('report.id'), nullable=False)
    tweeted = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    photo_downloaded = Column(Boolean, default=False, server_default=text('false'), nullable=False)
    thumb_downloaded = Column(Boolean, default=False, server_default=text('false'), nullable=False)

    def __repr__(self):
        return f'<Meta id={self.id!r}>'

