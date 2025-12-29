from simulation import simulate_30_days

def compute_spending_behavior(transactions):
    """Calculates average daily burn rate from history."""
    daily = {}
    for tx in transactions:
        if tx.type != "debit": continue
        # Use date as key
        d = tx.timestamp.date() if hasattr(tx.timestamp, 'date') else str(tx.timestamp)[:10]
        daily[d] = daily.get(d, 0) + tx.amount
    
    if not daily:
        return {"avg_daily": 0, "volatility": 0}
    
    values = list(daily.values())
    return {
        "avg_daily": sum(values) / len(values),
        "volatility": max(values) - min(values) if len(values) > 1 else 0
    }

def detect_risk(user_id: str, db, buffer_limit=500.0):
    simulation = simulate_30_days(user_id, db)
    if not simulation:
        return {"risk": False, "status": "safe"}

    current_balance = simulation[0]["balance"]
    
    # Check for buffer breach
    for day_data in simulation:
        if day_data["balance"] < buffer_limit:
            return {
                "risk": True,
                "status": "warning",
                "days_left": day_data["day"],
                "message": f"Balance will drop below ${buffer_limit} buffer."
            }

    return {"risk": False, "status": "safe"}