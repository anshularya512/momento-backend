import requests
import json

# Your Production URL
BASE_URL = "https://momento-backend-production-832d.up.railway.app"
USER_ID = "test_user_99"

# 1. Realistic Demo Data (Salary + Rent + Subscriptions + Snacks)
# This tests the Regex Parser and the Detectors (Salary/Netflix)
RAW_STATEMENT = """
01/10/2025 ACH SALARY DEPOSIT 3500.00
02/10/2025 RENT PAYMENT -1200.00
05/10/2025 NETFLIX SUBSCRIPTION -15.99
07/10/2025 ZOMATO FOOD ORDER -25.50
10/10/2025 STARBUCKS COFFEE -6.50
15/10/2025 UPWORK FREELANCE 200.00
20/10/2025 ELECTRIC BILL -110.00
"""

def run_test():
    print(f"🚀 Starting Momento System Check for: {BASE_URL}\n")

    # STEP 1: Health Check
    print("Checking API Health...")
    health = requests.get(f"{BASE_URL}/").json()
    print(f"✅ Backend Status: {health.get('status')}\n")

    # STEP 2: Upload Statement (Testing /transactions/statement)
    print("Uploading Demo Statement...")
    payload = {
        "user_id": USER_ID,
        "text": RAW_STATEMENT
    }
    upload_res = requests.post(f"{BASE_URL}/transactions/statement", json=payload)
    if upload_res.status_code == 200:
        print(f"✅ Upload Success: {upload_res.json()['inserted']} transactions parsed.\n")
    else:
        print(f"❌ Upload Failed: {upload_res.text}\n")
        return

    # STEP 3: Check Forecast (Testing /forecast/{user_id})
    # This verifies if the Salary and Burn Rate math is working
    print("Fetching Forecast & Risk Analysis...")
    forecast = requests.get(f"{BASE_URL}/forecast/{USER_ID}").json()
    
    print("-" * 30)
    print(f"💰 Current Balance: ${forecast.get('current_balance')}")
    print(f"🛡️ System State: {forecast.get('status').upper()}")
    print(f"📅 Safe Window: {forecast.get('days_until_zero')} days left")
    print(f"💡 Action Suggestion: {forecast.get('recommendation', {}).get('message')}")
    print("-" * 30)

    # STEP 4: Check Simulation (Testing /simulate/{user_id})
    print("\nVerifying 30-Day Predictive Model...")
    sim = requests.get(f"{BASE_URL}/simulate/{USER_ID}").json()
    if len(sim) >= 30:
        print(f"✅ Simulation Ready: Last predicted day balance: ${sim[-1]['balance']}")
    else:
        print("⚠️ Simulation incomplete.")

if __name__ == "__main__":
    run_test()