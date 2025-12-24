from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models_extra import RecurringTransaction, IncomeSource

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
@app.get("/debug/transactions")
def list_txns(db: Session = Depends(get_db)):
    txns = db.query(Transaction).all()
    return [
        {
            "user_id": t.user_id,
            "amount": t.amount,
            "type": t.type,
            "raw": t.raw,
            "timestamp": t.timestamp
        }
        for t in txns
    ]

from detectors import detect_salary, detect_subscriptions

@app.post("/transactions")
def ingest(txn: TxnIn, db: Session = Depends(get_db)):
    t = Transaction(**txn.dict())
    db.add(t)
    db.commit()

    detect_salary(txn.user_id, db)
    detect_subscriptions(txn.user_id, db)

    return {"ok": True}
from simulation import simulate_30_days

@app.get("/simulate/{user_id}")
def simulate(user_id: str, db: Session = Depends(get_db)):
    return simulate_30_days(user_id, db)


from risk import detect_risk

@app.get("/risk/{user_id}")
def risk(user_id: str, db: Session = Depends(get_db)):
    return detect_risk(user_id, db)


from actions import suggest_action

@app.get("/action/{user_id}")
def action(user_id: str, db: Session = Depends(get_db)):
    return suggest_action(user_id, db)
