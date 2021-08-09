from sqlalchemy import create_engine
from dotenv import dotenv_values

db = dotenv_values("db.dev.env")

db_url = f"mysql+pymysql://{db.get('DB_USER')}:{db.get('DB_PASSWORD')}@{db.get('DB_HOST')}:{db.get('DB_PORT')}/{db.get('DB_DATABASE')}?charset=utf8mb4"

engine = create_engine(db_url, echo=True, future=True)
