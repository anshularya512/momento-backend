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



from fastapi import UploadFile, File

@app.post("/upload-file/{user_id}")
async def upload_statement(user_id: str, file: UploadFile = File(...)):
    # This prepares the app to take a CSV or PDF
    contents = await file.read()
    # Logic to parse CSV text into transactions would go here
    return {"message": f"File {file.filename} received and queued for analysis"}



from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import Transaction
from detectors import detect_recurring_patterns
from risk import detect_risk
import io
import pandas as pd

app = FastAPI()

@app.post("/analyze/{user_id}")
async def analyze_statement(user_id: str, data: dict, db: Session = Depends(get_db)):
    # This handles the "Paste" functionality
    raw_text = data.get("text", "")
    if not raw_text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    # Simple parser for your pasted text format
    lines = raw_text.split('\n')
    for line in lines:
        if not line.strip() or line.startswith('#'): continue
        parts = line.split()
        if len(parts) >= 3:
            try:
                amt = float(parts[-1])
                new_tx = Transaction(
                    user_id=user_id,
                    raw=line,
                    amount=abs(amt),
                    type="credit" if amt > 0 else "debit"
                )
                db.add(new_tx)
            except: continue
    
    db.commit()
    
    # Learn patterns (Salary/Rent)
    detect_recurring_patterns(user_id, db)
    
    # Calculate Runway & Risk
    analysis = detect_risk(user_id, db)
    return analysis

@app.post("/upload-csv/{user_id}")
async def upload_csv(user_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    df = pd.read_csv(io.StringIO(content.decode('utf-8')))
    # Assume CSV has 'description' and 'amount'
    for _, row in df.iterrows():
        amt = float(row['amount'])
        db.add(Transaction(
            user_id=user_id, 
            raw=row['description'], 
            amount=abs(amt), 
            type="credit" if amt > 0 else "debit"
        ))
    db.commit()
    detect_recurring_patterns(user_id, db)
    return detect_risk(user_id, db)