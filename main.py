from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import time

from db import SessionLocal, engine, Base
import models, models_extra
from actions import parse_statement_text, suggest_action
from detectors import detect_recurring_patterns
from risk import detect_risk
from simulation import simulate_30_days

# Initialize DB
models.Base.metadata.create_all(bind=engine)
models_extra.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Forely API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.get("/")
def health(): return {"status": "Forely Backend Live", "epoch": int(time.time())}

@app.post("/transactions/statement")
def upload_statement(payload: models_extra.StatementUpload, db: Session = Depends(get_db)):
    parsed = parse_statement_text(payload.text)
    if not parsed: raise HTTPException(400, "No valid transactions found in text")
    
    user_id = str(payload.user_id)
    for row in parsed:
        tx = models.Transaction(
            user_id=user_id,
            amount=row["amount"],
            type=row["type"],
            raw=row["raw"],
            timestamp=int(row["timestamp"].timestamp())
        )
        db.add(tx)
    
    db.commit()
    detect_salary(user_id, db)
    detect_subscriptions(user_id, db)
    return {"inserted": len(parsed), "user_id": user_id}

@app.get("/forecast/{user_id}")
def get_forecast(user_id: str, db: Session = Depends(get_db)):
    risk_info = detect_risk(user_id, db)
    action_info = suggest_action(user_id, risk_info, db)
    
    # Calculate Balance
    txs = db.query(models.Transaction).filter(models.Transaction.user_id == user_id).all()
    balance = sum(t.amount if t.type == "credit" else -t.amount for t in txs)
    
    return {
        "status": "warning" if risk_info.get("risk") else "safe",
        "days_until_zero": risk_info.get("days_left", 30),
        "current_balance": round(balance, 2),
        "recommendation": action_info,
        "risk_cause": risk_info.get("cause", "variable spending")
    }

@app.get("/simulate/{user_id}")
def get_simulation(user_id: str, db: Session = Depends(get_db)):
    return simulate_30_days(user_id, db)



@app.get("/risk/{user_id}")
def risk(user_id: str, db: Session = Depends(get_db)): # Changed int to str
    return detect_risk(user_id, db)