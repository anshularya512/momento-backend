# actions.py

PAUSABLE_KEYWORDS = [
    "spotify", "netflix", "prime", "hotstar",
    "youtube", "apple", "google", "membership"
]

def is_pausable(merchant: str) -> bool:
    m = merchant.lower()
    return any(k in m for k in PAUSABLE_KEYWORDS)


from simulation import simulate_30_days, get_current_balance
from datetime import datetime, timedelta

def simulate_without(merchant: str, user_id: str, db):
    balance = get_current_balance(user_id, db)
    simulation = []

    today = datetime.utcnow().date()

    for day in range(1, 31):
        date = today + timedelta(days=day)

        # skip this merchant
        # other debits/credits assumed same
        simulation.append({
            "day": day,
            "balance": balance
        })

    return simulation



from models_extra import RecurringTransaction
from risk import detect_risk

def suggest_action(user_id: str, db):
    risk = detect_risk(user_id, db)

    if not risk.get("risk"):
        return {"action": None}

    recurrences = db.query(RecurringTransaction).filter(
        RecurringTransaction.user_id == user_id,
        RecurringTransaction.type == "debit"
    ).all()

    # sort by amount (smallest pain first)
    recurrences.sort(key=lambda r: r.amount)

    for r in recurrences:
        if is_pausable(r.merchant):
            return {
                "action": "pause",
                "target": r.merchant,
                "message": f"Pause {r.merchant.title()} → balance stays safe"
            }

    # fallback
    return {
        "action": "warn",
        "message": "Spending may need adjustment"
    }
