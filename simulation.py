# forely/simulation.py
def forecast_cash_window(balance, avg_daily, volatility, buffer=500.0):
    # If balance is already low, it's an immediate warning
    if balance < buffer:
        return {
            "range_days": [0, 2],
            "confidence": 0.99,
            "state": "warning"
        }

    if avg_daily == 0:
        return {"range_days": [30, 45], "confidence": 0.9, "state": "safe"}

    # Calculate when we hit the BUFFER, not just zero
    lower = int((balance - buffer) / (avg_daily + volatility * 0.3))
    
    return {
        "range_days": [max(lower, 0), lower + 5],
        "confidence": 0.75,
        "state": "warning" if lower < 10 else "stable"
    }g