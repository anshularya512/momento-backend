from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models_extra import RecurringTransaction, IncomeSource
from models_extra import DeviceToken
from db import engine, Base
from fastapi.middleware.cors import CORSMiddleware
import traceback
from fastapi.responses import PlainTextResponse

from db import SessionLocal, engine
from models import Base, Transaction
from models_extra import BulkTransaction
from actions import parse_statement_text
from risk import compute_spending_behavior
from simulation import forecast_cash_window


# 1️⃣ CREATE APP FIRST
app = FastAPI()
Base.metadata.create_all(bind=engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
class TokenIn(BaseModel):
    user_id: str
    token: str
@app.post("/register-token")
def register_token(data: TokenIn, db: Session = Depends(get_db)):
    exists = db.query(DeviceToken).filter(
        DeviceToken.token == data.token
    ).first()

    if not exists:
        db.add(DeviceToken(**data.dict()))
        db.commit()

    return {"ok": True}


from models_extra import StatementUpload
@app.post("/transactions/statement")
def upload_statement(payload: StatementUpload, db: Session = Depends(get_db)):
    try:
        parsed = parse_statement_text(payload.text)

        inserted = 0
        for row in parsed:
            tx = Transaction(
                user_id=payload.user_id,
                timestamp=row["timestamp"],
                amount=row["amount"],
                type=row["type"]
            )
            db.add(tx)
            inserted += 1

        db.commit()
        return {"inserted": inserted}

    except Exception as e:
        return PlainTextResponse(
            traceback.format_exc(),
            status_code=500
        )

@app.get("/analyze/statement")
def analyze_statement(user_id: int, db: Session = Depends(get_db)):
    txs = db.query(Transaction).filter(Transaction.user_id == user_id).all()

    if not txs:
        return {
            "avg_daily_burn": 0,
            "volatility": 0,
            "balance_estimate": 0,
            "forecast": {
                "range_days": [0, 0],
                "confidence": 0,
                "state": "no-data"
            }
        }

    behavior = compute_spending_behavior(txs)

    balance = 0
    for tx in txs:
        balance += tx.amount if tx.type == "credit" else -tx.amount

    forecast = forecast_cash_window(
        balance,
        behavior["avg_daily"],
        behavior["volatility"]
    )

    return {
        "avg_daily_burn": behavior["avg_daily"],
        "volatility": behavior["volatility"],
        "balance_estimate": balance,
        "forecast": forecast
    }




from models_extra import StatementUpload

@app.post("/transactions/statement")
def upload_statement(
    payload: StatementUpload,
    db: Session = Depends(get_db)
):
    parsed = parse_statement_text(payload.text)

    if not parsed:
        return {"inserted": 0}

    for row in parsed:
        tx = Transaction(
            user_id=payload.user_id,
            timestamp=row["timestamp"],
            amount=row["amount"],
            type=row["type"]
        )
        db.add(tx)

    db.commit()
    return {"inserted": len(parsed)}
