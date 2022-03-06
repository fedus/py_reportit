from sqlalchemy import Column, Unicode, Boolean, text
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy_utils.types.password import PasswordType
from arrow import Arrow
from uuid import uuid4

from py_reportit.shared.model.orm_base import Base
from py_reportit.shared.util.localized_arrow import LocalizedArrow


class User(Base):

    __tablename__ = 'user'

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid4)
    username = Column(Unicode(100), nullable=False, unique=True)
    password = Column(PasswordType(schemes=["pbkdf2_sha512"]), nullable=False)
    created_at = Column(LocalizedArrow, nullable=False, default=Arrow.now)
    last_login = Column(LocalizedArrow, nullable=True)
    admin = Column(Boolean, nullable=False, default=False, server_default=text('false'))
    disabled = Column(Boolean, nullable=False, default=False, server_default=text('false'))
