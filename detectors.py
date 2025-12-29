# forely/detectors.py
from sqlalchemy.orm import Session
from models import Transaction
from models_extra import IncomeSource, RecurringTransaction
from collections import defaultdict

def detect_recurring_patterns(user_id: str, db: Session):
    txns = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    patterns = defaultdict(list)
    
    for tx in txns:
        # Grouping by amount and type to find recurring bills/salary
        key = f"{tx.type}_{tx.amount}"
        patterns[key].append(tx)

    for key, items in patterns.items():
        tx = items[0]
        if tx.type == "credit":
            exists = db.query(IncomeSource).filter(IncomeSource.user_id == user_id).first()
            if not exists:
                db.add(IncomeSource(user_id=user_id, amount=tx.amount, interval_days=30))
        else:
            exists = db.query(RecurringTransaction).filter(
                RecurringTransaction.user_id == user_id, 
                RecurringTransaction.amount == tx.amount
            ).first()
            if not exists:
                db.add(RecurringTransaction(
                    user_id=user_id,
                    merchant=tx.raw[:20],
                    amount=tx.amount,
                    interval_days=30,
                    type="debit"
                ))
    db.commit()