from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from py_reportit.shared.config import config

db_url = f"mysql+pymysql://{config.get('DB_USER')}:{config.get('DB_PASSWORD')}@{config.get('DB_HOST')}:{config.get('DB_PORT')}/{config.get('DB_DATABASE')}?charset=utf8mb4"

engine = create_engine(db_url, pool_recycle=400, echo=config.get("LOG_LEVEL") == "DEBUG", future=True)

SessionLocal = sessionmaker(engine)