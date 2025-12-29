from simulation import simulate_30_days

def detect_risk(user_id: str, db, buffer_limit=500.0):
    # This runs a 30-day "Future Simulation"
    simulation = simulate_30_days(user_id, db)
    
    if not simulation:
        return {"risk": False, "status": "safe", "message": "No data to analyze."}

    # Get the lowest balance predicted in the next 30 days
    min_balance = min([day["balance"] for day in simulation])
    current_balance = simulation[0]["balance"]

    if min_balance < buffer_limit:
        return {
            "risk": True,
            "status": "warning",
            "days_left": next((d["day"] for d in simulation if d["balance"] < buffer_limit), 0),
            "message": f"Danger: Your balance will drop to ${round(min_balance, 2)} which is below your safety buffer.",
            "current_balance": current_balance
        }

    return {
        "risk": False, 
        "status": "safe", 
        "message": "You are within your safe spending zone.",
        "current_balance": current_balance
    }