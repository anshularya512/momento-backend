from simulation import simulate_30_days, get_future_events

def detect_risk(user_id: str, db):
    simulation = simulate_30_days(user_id, db)
    events = get_future_events(user_id, db)

    for day_data in simulation:
        if day_data["balance"] <= 0:
            risk_day = day_data["date"]

            causes = [
                e for e in events
                if str(e["date"]) == risk_day and e["type"] == "debit"
            ]

            cause = causes[0]["source"] if causes else "spending"

            return {
                "risk": True,
                "days_left": day_data["day"],
                "date": risk_day,
                "cause": cause
            }

    return {
        "risk": False
    }
