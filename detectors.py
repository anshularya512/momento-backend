from sqlalchemy.orm import Session
from models import Transaction
from models_extra import IncomeSource, RecurringTransaction
from collections import defaultdict

def detect_recurring_patterns(user_id: str, db: Session):
    # Fetch all transactions for this user
    txns = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    
    # Map to track frequency of similar transactions
    patterns = defaultdict(list)
    
    for tx in txns:
        # Group by a simplified merchant name and amount
        # This helps identify Rent or Salary even if the date varies slightly
        key = f"{tx.type}_{tx.amount}"
        patterns[key].append(tx)

    for key, items in patterns.items():
        if len(items) >= 1: # MVP: Treat even single large entries as patterns
            tx = items[0]
            if tx.type == "credit":
                # Save as an Income Source
                exists = db.query(IncomeSource).filter(IncomeSource.user_id == user_id).first()
                if not exists:
                    db.add(IncomeSource(user_id=user_id, amount=tx.amount, interval_days=30))
            else:
                # Save as a Recurring Expense
                exists = db.query(RecurringTransaction).filter(
                    RecurringTransaction.user_id == user_id, 
                    RecurringTransaction.amount == tx.amount
                ).first()
                if not exists:
                    db.add(RecurringTransaction(
                        user_id=user_id,
                        merchant=tx.raw[:20], # Use start of raw text as merchant name
                        amount=tx.amount,
                        interval_days=30,
                        type="debit"
                    ))
    db.commit()