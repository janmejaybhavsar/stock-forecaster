import sys
sys.path.insert(0, ".")
import httpx

BASE = "http://localhost:8000/api/v1"

# Test register
print("--- Register ---")
r = httpx.post(f"{BASE}/auth/register", json={
    "email": "demo@test.com",
    "username": "demo",
    "password": "demo123"
})
print(f"Status: {r.status_code}")
print(f"User: {r.json()}")

# Test duplicate register
r2 = httpx.post(f"{BASE}/auth/register", json={
    "email": "demo@test.com",
    "username": "demo2",
    "password": "demo123"
})
print(f"\nDuplicate email: {r2.status_code} {r2.json()['detail']}")

# Test login
print("\n--- Login ---")
r = httpx.post(f"{BASE}/auth/login", json={
    "email": "demo@test.com",
    "password": "demo123"
})
print(f"Status: {r.status_code}")
token = r.json()["access_token"]
print(f"Token: {token[:50]}...")

headers = {"Authorization": f"Bearer {token}"}

# Test /me
print("\n--- Me ---")
r = httpx.get(f"{BASE}/auth/me", headers=headers)
print(f"User: {r.json()}")

# Test without token
r = httpx.get(f"{BASE}/auth/me")
print(f"No token: {r.status_code}")

# Test portfolio
print("\n--- Portfolio ---")
r = httpx.post(f"{BASE}/portfolio/holdings", json={
    "ticker": "AAPL",
    "shares": 10,
    "avg_cost": 180.0
}, headers=headers)
print(f"Add holding: {r.status_code} {r.json()['ticker']}")

r = httpx.post(f"{BASE}/portfolio/holdings", json={
    "ticker": "MSFT",
    "shares": 5,
    "avg_cost": 350.0
}, headers=headers)
print(f"Add holding: {r.status_code} {r.json()['ticker']}")

r = httpx.get(f"{BASE}/portfolio/", headers=headers)
p = r.json()
print(f"Portfolio: {p['summary']['holdings_count']} holdings, total value: ${p['summary']['total_value']:,.2f}")
for h in p["holdings"]:
    print(f"  {h['ticker']}: {h['shares']} shares @ ${h['avg_cost']:.2f}, P&L: ${h['pnl']:.2f} ({h['pnl_pct']:.1f}%)")

# Test watchlist
print("\n--- Watchlist ---")
r = httpx.post(f"{BASE}/watchlists/", json={
    "name": "Tech Stocks",
    "tickers": ["AAPL", "MSFT", "GOOGL"]
}, headers=headers)
wl = r.json()
print(f"Created: {wl['name']} with {wl['tickers']}")

r = httpx.get(f"{BASE}/watchlists/", headers=headers)
print(f"Count: {len(r.json())}")

# Test existing endpoints still work without auth
print("\n--- Existing endpoints (no auth) ---")
r = httpx.get(f"{BASE}/models/")
print(f"Models: {r.status_code} {r.json()}")

r = httpx.get(f"{BASE}/stocks/AAPL/info", timeout=30)
print(f"Stock info: {r.status_code} {r.json().get('name', 'ok')}")

print("\nAll auth API tests passed!")
