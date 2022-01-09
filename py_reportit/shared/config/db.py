import logging

from typing import Iterable
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker as sqlalchemy_sessionmaker
from sqlalchemy.orm.session import Session

logger = logging.getLogger(f"py_reportit.{__name__}")

class Database:

    def __init__(self, log_db, **kwargs):
        self.db_url = self.get_db_url(**kwargs)
        self.engine = create_engine(self.db_url, pool_recycle=400, echo=int(log_db), future=True)
        self.sqlalchemy_sessionmaker = sqlalchemy_sessionmaker(self.engine)

    @staticmethod
    def get_db_url(db_user, db_password, db_host, db_port, db_database) -> str:
        return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}?charset=utf8mb4"

def get_session(database: Database) -> Iterable[Session]:
    logger.debug("Getting session ...")
    with database.sqlalchemy_sessionmaker() as session:
        logger.debug("Yielding session")
        yield session
    logger.debug("Closing session")
