# simulation.py
from sqlalchemy.orm import Session
from models import Transaction
from models_extra import IncomeSource, RecurringTransaction
from datetime import datetime, timedelta

def get_current_balance(user_id: str, db: Session) -> float:
    txns = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()

    balance = 0.0
    for t in txns:
        if t.type == "credit":
            balance += t.amount
        else:
            balance -= t.amount

    return balance

def get_future_events(user_id: str, db: Session):
    events = []

    incomes = db.query(IncomeSource).filter(
        IncomeSource.user_id == user_id
    ).all()

    recurrences = db.query(RecurringTransaction).filter(
        RecurringTransaction.user_id == user_id
    ).all()

    today = datetime.utcnow().date()

    for inc in incomes:
        next_date = today + timedelta(days=inc.interval_days)
        events.append({
            "date": next_date,
            "amount": inc.amount,
            "type": "credit",
            "source": "income"
        })

    for rec in recurrences:
        next_date = today + timedelta(days=rec.interval_days)
        events.append({
            "date": next_date,
            "amount": rec.amount,
            "type": "debit",
            "source": rec.merchant
        })

    return events


def simulate_30_days(user_id: str, db: Session):
    balance = get_current_balance(user_id, db)
    events = get_future_events(user_id, db)

    today = datetime.utcnow().date()
    simulation = []

    for day in range(1, 31):
        date = today + timedelta(days=day)

        for e in events:
            if e["date"] == date:
                if e["type"] == "credit":
                    balance += e["amount"]
                else:
                    balance -= e["amount"]

        simulation.append({
            "day": day,
            "date": str(date),
            "balance": round(balance, 2)
        })

    return simulation



def forecast_cash_window(balance, avg_daily, volatility):
    if avg_daily == 0:
        return {
            "range_days": [30, 45],
            "confidence": 0.9,
            "state": "safe"
        }

    lower = int(balance / (avg_daily + volatility * 0.3))
    upper = int(balance / max(avg_daily - volatility * 0.3, 1))

    return {
        "range_days": [max(lower, 1), max(upper, lower + 3)],
        "confidence": 0.75,
        "state": "warning" if lower < 10 else "stable"
    }
