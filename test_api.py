import time
import httpx

BASE = "http://localhost:8000/api/v1"

print("=== Testing Stock History ===")
r = httpx.get(f"{BASE}/stocks/AAPL/history", params={"start": "2025-05-01", "end": "2025-05-20"}, timeout=30)
print(f"Status: {r.status_code}, Records: {len(r.json())}")

print("\n=== Testing Models List ===")
r = httpx.get(f"{BASE}/models", timeout=30)
print(f"Models: {r.json()}")

print("\n=== Testing ARIMA Forecast ===")
r = httpx.post(f"{BASE}/forecasts/run", json={"ticker": "AAPL", "model_name": "arima", "horizon": 5}, timeout=30)
job = r.json()
fid = job["id"]
print(f"Job started: {fid}")

for _ in range(60):
    time.sleep(2)
    r = httpx.get(f"{BASE}/forecasts/{fid}", timeout=30)
    result = r.json()
    if result["status"] != "running":
        break

print(f"Status: {result['status']}")
if result.get("predictions"):
    for p in result["predictions"]:
        print(f"  {p}")
if result.get("error"):
    print(f"Error: {result['error']}")

print("\nDone!")
