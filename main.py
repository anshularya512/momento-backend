from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db import SessionLocal, engine
from models import Base, Transaction


# 1️⃣ CREATE APP FIRST
app = FastAPI()


# 2️⃣ CREATE TABLES ON STARTUP
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


# 3️⃣ DB SESSION DEPENDENCY
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 4️⃣ INPUT SCHEMA
class TxnIn(BaseModel):
    user_id: str
    amount: float
    type: str
    raw: str
    timestamp: int


# 5️⃣ HEALTH CHECK
@app.get("/")
def health():
    return {"status": "backend live"}


# 6️⃣ TRANSACTION INGESTION
@app.post("/transactions")
def ingest(txn: TxnIn, db: Session = Depends(get_db)):
    t = Transaction(**txn.dict())
    db.add(t)
    db.commit()
    return {"ok": True}
