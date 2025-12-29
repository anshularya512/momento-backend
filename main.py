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

# Import pandas safely
try:
    import pandas as pd
except ImportError:
    pd = None

# Local Imports 
from db import SessionLocal, engine
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
    try: yield db
    finally: db.close()

@app.get("/")
def health(): 
    return {"status": "Forely Backend Live", "pandas_loaded": pd is not None}

@app.post("/analyze/{user_id}")
async def analyze_statement(user_id: str, data: dict, db: Session = Depends(get_db)):
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
    if pd is None:
        raise HTTPException(500, "Pandas library not installed on server")
    
    content = await file.read()
    df = pd.read_csv(io.StringIO(content.decode('utf-8')))
    
    for _, row in df.iterrows():
        try:
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

# Keep original endpoints for frontend compatibility
@app.get("/forecast/{user_id}")
def get_forecast(user_id: str, db: Session = Depends(get_db)):
    risk_info = detect_risk(user_id, db)
    return risk_info