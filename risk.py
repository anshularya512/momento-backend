from simulation import simulate_30_days

def detect_risk(user_id: str, db, buffer_limit=500.0):
    simulation = simulate_30_days(user_id, db)
    if not simulation: return {"status": "safe"}

    current_balance = simulation[0]["balance"]
    # Find the day the balance drops below the buffer
    for day in simulation:
        if day["balance"] < buffer_limit:
            days_left = day["day"]
            return {
                "status": "warning",
                "days_remaining": days_left,
                "message": f"You'll breach your safety buffer in {days_left} days. Avoid non-essential spending."
            }
            
    return {"status": "safe", "days_remaining": 30}