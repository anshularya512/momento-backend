from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import datetime
import calendar
import traceback

from db import SessionLocal, engine
from models import Base, Transaction
from models_extra import (
    StatementUpload,
    DeviceToken
)

from actions import parse_statement_text, suggest_action
from detectors import detect_salary, detect_subscriptions
from risk import compute_spending_behavior, detect_risk
from simulation import forecast_cash_window, simulate_30_days


# ================================
# APP INITIALIZATION
# ================================

app = FastAPI(title="Momento Backend")

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================
# DATABASE DEPENDENCY
# ================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================================
# UTILS
# ================================

def to_epoch(dt: datetime.datetime) -> int:
    """
    Convert datetime -> UTC epoch seconds (BIGINT safe)
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return int(calendar.timegm(dt.utctimetuple()))


# ================================
# HEALTH CHECK
# ================================

@app.get("/")
def health():
    return {"status": "backend live"}


# ================================
# TOKEN REGISTRATION (PUSH)
# ================================

class TokenIn(BaseModel):
    user_id: int
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


# ================================
# STATEMENT INGESTION (TEXT / SMS / PDF PARSED TEXT)
# ================================

@app.post("/transactions/statement")
def upload_statement(payload: StatementUpload, db: Session = Depends(get_db)):
    try:
        parsed = parse_statement_text(payload.text)

        if not parsed:
            return {"inserted": 0}

        inserted = 0

        for row in parsed:
            tx = Transaction(
                user_id=payload.user_id,
                amount=row["amount"],
                type=row["type"],
                raw=row.get("raw"),
                timestamp=to_epoch(row["timestamp"])  # 🔥 FIXED
            )
            db.add(tx)
            inserted += 1

        db.commit()

        # Run detectors AFTER commit
        detect_salary(payload.user_id, db)
        detect_subscriptions(payload.user_id, db)

        return {"inserted": inserted}

    except Exception:
        db.rollback()
        return PlainTextResponse(
            traceback.format_exc(),
            status_code=500
        )


# ================================
# ANALYSIS ENDPOINT
# ================================

@app.get("/analyze/statement")
def analyze_statement(user_id: int, db: Session = Depends(get_db)):
    txs = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()

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


# ================================
# RISK / SIMULATION / ACTIONS
# ================================

@app.get("/risk/{user_id}")
def risk(user_id: int, db: Session = Depends(get_db)):
    return detect_risk(user_id, db)


@app.get("/simulate/{user_id}")
def simulate(user_id: int, db: Session = Depends(get_db)):
    return simulate_30_days(user_id, db)


@app.get("/action/{user_id}")
def action(user_id: int, db: Session = Depends(get_db)):
    return suggest_action(user_id, db)


# ================================
# DEBUG (REMOVE IN PROD LATER)
# ================================

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
