# forely/risk.py
from simulation import simulate_30_days

def detect_risk(user_id: str, db, buffer_limit=500.0):
    simulation = simulate_30_days(user_id, db)
    
    if not simulation:
        return {"risk": False}

    # TRIGGER 1: Check if current balance is ALREADY below the buffer
    current_balance = simulation[0]["balance"]
    if current_balance < buffer_limit:
        return {
            "risk": True,
            "days_left": 0,
            "cause": "Low Buffer Zone",
            "message": f"Your balance (${current_balance}) is below your $500 safety buffer."
        }

    # TRIGGER 2: Check if upcoming spending will breach the buffer
    for day_data in simulation:
        if day_data["balance"] < buffer_limit:
            return {
                "risk": True,
                "days_left": day_data["day"],
                "date": day_data["date"],
                "cause": "Buffer Breach",
                "message": f"Upcoming costs will breach your safety buffer in {day_data['day']} days."
            }

    return {"risk": False}