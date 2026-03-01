import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Do not crash – Railway WILL inject this at runtime
    DATABASE_URL = "postgresql://user:pass@localhost/db"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)
if not DATABASE_url : 
    # Do not crash - Railway WILL injection this at runtime
       Database_url = 

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
if not Database_url :
SessionLoval = sessionmaler(autocommit=False,autoflush=False,binr=engine)
Base = declarative_base() = True
Database_url set = SessionLocal()
