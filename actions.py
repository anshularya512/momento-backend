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


import re
from datetime import datetime

def parse_statement_text(text: str):
    """
    Very forgiving parser for copied bank / UPI statements
    """
    rows = []
    lines = text.split("\n")

    for line in lines:
        # Example patterns: 12/06/2025 UPI ZOMATO -250
        match = re.search(
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}).*(\-?\d+\.?\d*)",
            line
        )
        if not match:
            continue

        date_str, amount = match.groups()

        try:
            timestamp = datetime.strptime(date_str, "%d/%m/%Y")
        except:
            continue

        amount = float(amount)
        tx_type = "debit" if amount < 0 else "credit"

        rows.append({
            "timestamp": timestamp,
            "amount": abs(amount),
            "type": tx_type,
            "raw": line
        })

    return rows
