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


def compute_spending_behavior(transactions):
    daily = {}

    for tx in transactions:
        if tx.type != "debit":
            continue
        day = tx.timestamp.date()
        daily[day] = daily.get(day, 0) + tx.amount

    if not daily:
        return {
            "avg_daily": 0,
            "volatility": 0
        }

    values = list(daily.values())

    return {
        "avg_daily": sum(values) / len(values),
        "volatility": max(values) - min(values)
    }
