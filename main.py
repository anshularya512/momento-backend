import sys
import os
import time
import io
from datetime import datetime

# --- CRITICAL FIX: Ensures Railway finds your local modules ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd

# Local Imports
from db import SessionLocal, engine, Base
import models
import models_extra
from actions import parse_statement_text, suggest_action
from detectors import detect_recurring_patterns
from risk import detect_risk
from simulation import simulate_30_days

# Initialize DB Tables
models.Base.metadata.create_all(bind=engine)
models_extra.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Forely Advanced API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 1. ORIGINAL ROUTES ---

@app.get("/")
def health(): 
    return {"status": "Forely Backend Live", "epoch": int(time.time())}

@app.post("/transactions/statement")
def upload_statement_original(payload: models_extra.StatementUpload, db: Session = Depends(get_db)):
    parsed = parse_statement_text(payload.text)
    if not parsed: 
        raise HTTPException(400, "No valid transactions found in text")
    
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
    # Updated to the new universal detector
    detect_recurring_patterns(user_id, db)
    return {"inserted": len(parsed), "user_id": user_id}

@app.get("/forecast/{user_id}")
def get_forecast(user_id: str, db: Session = Depends(get_db)):
    risk_info = detect_risk(user_id, db)
    action_info = suggest_action(user_id, risk_info, db)
    
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
def risk_check(user_id: str, db: Session = Depends(get_db)):
    return detect_risk(user_id, db)

# --- 2. ADVANCED NEW FEATURES ---

@app.post("/analyze/{user_id}")
async def analyze_statement(user_id: str, data: dict, db: Session = Depends(get_db)):
    """Advanced 'Paste' logic: Learns patterns and predicts runway."""
    raw_text = data.get("text", "")
    if not raw_text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    lines = raw_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'): continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                # Get the last number as the amount
                amt = float(parts[-1].replace('+', '').replace(',', ''))
                new_tx = models.Transaction(
                    user_id=user_id,
                    raw=line,
                    amount=abs(amt),
                    type="credit" if amt > 0 else "debit",
                    timestamp=int(datetime.utcnow().timestamp())
                )
                db.add(new_tx)
            except: continue
    
    db.commit()
    detect_recurring_patterns(user_id, db)
    analysis = detect_risk(user_id, db)
    
    return {
        "status": "warning" if analysis.get("risk") else "safe",
        "days_remaining": analysis.get("days_left", 30),
        "message": analysis.get("message", "Runway calculated."),
        "current_balance": analysis.get("current_balance")
    }

@app.post("/upload-csv/{user_id}")
async def upload_csv(user_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Accepts bank CSVs and performs full month analysis."""
    content = await file.read()
    df = pd.read_csv(io.StringIO(content.decode('utf-8')))
    
    for _, row in df.iterrows():
        try:
            # Flexible column detection
            amt = float(row.get('amount', row.get('Amount', 0)))
            desc = str(row.get('description', row.get('Description', 'Bank Tx')))
            
            db.add(models.Transaction(
                user_id=user_id, 
                raw=desc, 
                amount=abs(amt), 
                type="credit" if amt > 0 else "debit",
                timestamp=int(datetime.utcnow().timestamp())
            ))
        except: continue
        
    db.commit()
    detect_recurring_patterns(user_id, db)
    return detect_risk(user_id, db)