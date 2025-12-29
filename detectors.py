from sqlalchemy.orm import Session
from models import Transaction
from models_extra import IncomeSource, RecurringTransaction

def detect_salary(user_id: str, db: Session):
    # Detect salary if 'salary' appears in the raw text
    salary_tx = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.raw.ilike("%salary%")
    ).first()
    
    if salary_tx:
        # Check if already exists to avoid duplicates
        exists = db.query(IncomeSource).filter(IncomeSource.user_id == user_id).first()
        if not exists:
            income = IncomeSource(user_id=user_id, amount=salary_tx.amount, interval_days=30, confidence=1.0)
            db.add(income)
            db.commit()

def detect_subscriptions(user_id: str, db: Session):
    # Detect Rent and common subs immediately
    keywords = ["rent", "netflix", "spotify", "gym", "prime", "apple", "google"]
    txns = db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.type == "debit").all()
    
    for tx in txns:
        for kw in keywords:
            if kw in tx.raw.lower():
                # Check if this specific merchant is already tracked
                exists = db.query(RecurringTransaction).filter(
                    RecurringTransaction.user_id == user_id, 
                    RecurringTransaction.merchant.ilike(f"%{kw}%")
                ).first()
                
                if not exists:
                    rec = RecurringTransaction(
                        user_id=user_id,
                        merchant=kw.capitalize(),
                        amount=tx.amount,
                        interval_days=30,
                        type="debit",
                        confidence=0.9
                    )
                    db.add(rec)
    db.commit()