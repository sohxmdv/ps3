# backend/test_api.py
import requests
import json

def test_simulation():
    url = "http://localhost:8000/api/simulate"
    
    # These are the default parameters we defined in main.py
    payload = {
        "initial_capital": 1000000,
        "sma_short_window": 10,
        "sma_long_window": 50,
        "var_confidence": 0.95,
        "max_position_size": 0.25,
        "transaction_fee_rate": 0.001,
        "slippage_base_rate": 0.0005
    }

    print(f"[*] Sending simulation request to {url}...")
    print("[*] The engine is processing ~27 years of data. This may take 2-5 seconds...\n")
    
    try:
        response = requests.post(url, json=payload)
        
        # Check if the server threw a 500 error
        response.raise_for_status() 
        
        data = response.json()

        print("✅ === SIMULATION SUCCESS === ✅\n")
        
        print("📊 [PORTFOLIO SUMMARY]")
        print(json.dumps(data['summary'], indent=2))
        
        print(f"\n📈 [FIRST 3 TRADES (Out of {len(data['trades'])} total)]")
        print(json.dumps(data['trades'][:3], indent=2))

        print(f"\n📉 [LAST 3 DAYS OF PORTFOLIO VALUE]")
        print(json.dumps(data['daily_values'][-3:], indent=2))
        
        print("\n🚀 Copy and paste this output into the chat!")

    except requests.exceptions.RequestException as e:
        print("❌ === SIMULATION FAILED === ❌\n")
        print(f"Error: {e}")
        if hasattr(response, 'text'):
            print(f"Response details: {response.text}")
            
if __name__ == "__main__":
    test_simulation()