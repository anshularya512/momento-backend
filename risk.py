from simulation import simulate_30_days

def detect_risk(user_id: str, db, buffer_limit=500.0):
    simulation = simulate_30_days(user_id, db)
    if not simulation:
        return {"status": "safe", "message": "No data found."}

    current_balance = simulation[0]["balance"]
    
    # Logic: Warning if current balance is below $500 
    # OR if the lowest point in the next 30 days is below $500
    min_future_balance = min([day["balance"] for day in simulation])

    if current_balance < buffer_limit or min_future_balance < buffer_limit:
        return {
            "status": "warning",
            "current_balance": current_balance,
            "min_forecasted": min_future_balance,
            "message": f"Cash Stress! Balance will drop to ${min_future_balance}."
        }

    return {
        "status": "safe",
        "current_balance": current_balance,
        "message": "Your cash flow looks healthy for the next 30 days."
    }