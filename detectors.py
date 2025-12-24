# detectors.py
from sqlalchemy.orm import Session
from models import Transaction
from models_extra import IncomeSource
from datetime import datetime
from collections import defaultdict


def detect_salary(user_id: str, db: Session):
    credits = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "credit"
        )
        .all()
    )

    if len(credits) < 2:
        return

    # group by approximate amount
    buckets = defaultdict(list)
    for c in credits:
        key = round(c.amount, -2)  # 12000 → 12000, 12345 → 12300
        buckets[key].append(c)

    for amount, txns in buckets.items():
        if len(txns) >= 2:
            interval = abs(txns[-1].timestamp - txns[-2].timestamp) // (60 * 60 * 24)
            if 25 <= interval <= 35:
                income = IncomeSource(
                    user_id=user_id,
                    amount=amount,
                    interval_days=interval,
                    confidence=0.9
                )
                db.add(income)
                db.commit()
                return


from models_extra import RecurringTransaction


def detect_subscriptions(user_id: str, db: Session):
    debits = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "debit"
        )
        .all()
    )

    buckets = defaultdict(list)

    for d in debits:
        merchant_key = d.raw.lower().split()[0]
        amount_key = round(d.amount, -1)
        buckets[(merchant_key, amount_key)].append(d)

    for (merchant, amount), txns in buckets.items():
        if len(txns) >= 2:
            interval = abs(txns[-1].timestamp - txns[-2].timestamp) // (60 * 60 * 24)
            if 25 <= interval <= 35:
                rec = RecurringTransaction(
                    user_id=user_id,
                    merchant=merchant,
                    amount=amount,
                    interval_days=interval,
                    type="debit",
                    confidence=0.85
                )
                db.add(rec)
                db.commit()
