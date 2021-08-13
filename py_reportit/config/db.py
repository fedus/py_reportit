from sqlalchemy import create_engine

from py_reportit.config import config

db_url = f"mysql+pymysql://{config.get('DB_USER')}:{config.get('DB_PASSWORD')}@{config.get('DB_HOST')}:{config.get('DB_PORT')}/{config.get('DB_DATABASE')}?charset=utf8mb4"

engine = create_engine(db_url, echo=True, future=True)
