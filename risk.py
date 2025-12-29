# forely/risk.py
from simulation import simulate_30_days

def compute_spending_behavior(transactions):
    """Calculates average daily burn rate from history."""
    daily = {}
    for tx in transactions:
        if tx.type != "debit": continue
        day = tx.timestamp # assuming this is already a date object or handled
        daily[day] = daily.get(day, 0) + tx.amount
    
    if not daily:
        return {"avg_daily": 0, "volatility": 0}
    
    values = list(daily.values())
    return {
        "avg_daily": sum(values) / len(values),
        "volatility": max(values) - min(values)
    }

def detect_risk(user_id: str, db, buffer_limit=500.0):
    simulation = simulate_30_days(user_id, db)
    if not simulation:
        return {"risk": False}

    current_balance = simulation[0]["balance"]
    if current_balance < buffer_limit:
        return {
            "risk": True,
            "days_left": 0,
            "cause": "Low Buffer Zone",
            "message": f"Your balance (${current_balance}) is below your $500 safety buffer."
        }

    for day_data in simulation:
        if day_data["balance"] < buffer_limit:
            return {
                "risk": True,
                "days_left": day_data["day"],
                "cause": "Buffer Breach",
                "message": f"Upcoming costs will breach your safety buffer in {day_data['day']} days."
            }
    return {"risk": False}