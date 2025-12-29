from sqlalchemy.orm import Session
import models
import models_extra

def detect_recurring_patterns(user_id: str, db: Session):
    # Fetch all history for this user
    txns = db.query(models.Transaction).filter(models.Transaction.user_id == user_id).all()
    if not txns:
        return

    # 1. Identify Salary (Highest Credit)
    credits = [t for t in txns if t.type == 'credit']
    if credits:
        top_income = max(credits, key=lambda x: x.amount)
        # Check if already exists to avoid duplicates
        if not db.query(models_extra.IncomeSource).filter_by(user_id=user_id).first():
            db.add(models_extra.IncomeSource(user_id=user_id, amount=top_income.amount, interval_days=30))

    # 2. Identify Major Bills (Debits > $500 like Rent)
    debits = [t for t in txns if t.type == 'debit' and t.amount > 500]
    for d in debits:
        existing = db.query(models_extra.RecurringTransaction).filter_by(user_id=user_id, amount=d.amount).first()
        if not existing:
            db.add(models_extra.RecurringTransaction(
                user_id=user_id,
                merchant=d.raw[:20],
                amount=d.amount,
                interval_days=30,
                type="debit"
            ))
    
    db.commit()