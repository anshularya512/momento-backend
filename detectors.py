from sqlalchemy.orm import Session
from models import Transaction
from models_extra import IncomeSource, RecurringTransaction

def detect_recurring_patterns(user_id: str, db: Session):
    # Get all history to learn behavior
    txns = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    
    # Simple logic: If a high-value debit (>30% of total) appears, treat it as Rent/Major Bill
    total_credit = sum([t.amount for t in txns if t.type == 'credit'])
    
    for tx in txns:
        if tx.type == 'credit' and tx.amount > (total_credit * 0.5):
            # Identified as primary Salary
            db.add(IncomeSource(user_id=user_id, amount=tx.amount, interval_days=30))
        elif tx.type == 'debit' and tx.amount > 500:
            # Identified as a Major Recurring Cost (Rent/Mortgage)
            db.add(RecurringTransaction(user_id=user_id, merchant=tx.raw[:15], amount=tx.amount, interval_days=30, type='debit'))
    db.commit()