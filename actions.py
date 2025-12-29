import re
from datetime import datetime
import calendar

PAUSABLE_KEYWORDS = ["spotify", "netflix", "prime", "hotstar", "youtube", "apple", "google", "membership", "gym"]

def parse_statement_text(text: str):
    rows = []
    lines = text.split("\n")
    for line in lines:
        # Matches: 12/10/2025, 12-10-2025, or 2025/10/12 + Amount
        match = re.search(r"(\d{1,4}[/-]\d{1,2}[/-]\d{1,4}).*?(\d+\.?\d*)", line)
        if not match: continue
        
        date_str, amt_str = match.groups()
        try:
            # Flexible date parsing
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%m/%d/%Y"):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    break
                except: continue
            else: continue
            
            amount = float(amt_str)
            # Heuristic: If 'cr' or 'salary' in line, it's credit. Else if '-' or 'dr' it's debit.
            tx_type = "credit" if any(x in line.lower() for x in ["cr", "salary", "refund", "dep"]) else "debit"
            
            rows.append({
                "timestamp": dt,
                "amount": abs(amount),
                "type": tx_type,
                "raw": line.strip()
            })
        except: continue
    return rows

def suggest_action(user_id: str, risk_data: dict, db):
    if not risk_data.get("risk"):
        return {"action": "none", "message": "You're safe for now."}

    from models_extra import RecurringTransaction
    recurrences = db.query(RecurringTransaction).filter(RecurringTransaction.user_id == user_id).all()
    
    for r in recurrences:
        if any(k in r.merchant.lower() for k in PAUSABLE_KEYWORDS):
            return {
                "action": "pause",
                "target": r.merchant,
                "message": f"If you pause {r.merchant}, you'll stay safe for {risk_data['days_left'] + 5} more days."
            }
    
    return {"action": "warn", "message": "High spending detected. Try to reduce non-essentials this week."}