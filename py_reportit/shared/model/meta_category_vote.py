from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types.uuid import UUIDType
from arrow import Arrow

from py_reportit.shared.model.orm_base import Base
from py_reportit.shared.util.localized_arrow import LocalizedArrow

class MetaCategoryVote(Base):

    __tablename__ = "category_vote"

    meta_id = Column(Integer, ForeignKey('meta.id'), primary_key=True)
    user_id = Column(UUIDType(binary=False), primary_key=True)
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    category = relationship("Category")
    timestamp = Column(LocalizedArrow, default=Arrow.now(), nullable=False)
