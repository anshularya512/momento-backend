from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db import SessionLocal
from models import Transaction

class TxnIn(BaseModel):
    user_id: str
    amount: float
    type: str
    raw: str
    timestamp: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/transactions")
def ingest(txn: TxnIn, db: Session = Depends(get_db)):
    t = Transaction(**txn.dict())
    db.add(t)
    db.commit()
    return {"ok": True}
