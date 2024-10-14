from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

try:
    SQL_DB_FILENAME = os.getenv("SQL_DB_FILENAME")
    SQLALCHEMY_DATABASE_URL = "sqlite:///"+SQL_DB_FILENAME
    
except Exception as e:
    SQLALCHEMY_DATABASE_URL = "sqlite:////app/db/app.db"
    print('creating new db @', SQLALCHEMY_DATABASE_URL)



engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

Base = declarative_base()
event.listen(engine, 'connect', lambda c, _: c.execute('pragma foreign_keys=on'))