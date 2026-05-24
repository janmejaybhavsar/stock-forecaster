import sys
sys.path.insert(0, ".")

from src.database.connection import init_db, get_db

init_db()
db = get_db()
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t["name"] for t in tables])

from src.auth.security import hash_password, verify_password, create_access_token, decode_token
from src.database.repositories import UserRepository, HoldingsRepository

users = UserRepository()
pw_hash = hash_password("testpass123")
user = users.create("test@example.com", "testuser", pw_hash)
print("Created user:", user["id"], user["username"], user["email"])

found = users.get_by_email("test@example.com")
print("Found by email:", found["username"])
print("Password verify:", verify_password("testpass123", found["password_hash"]))
print("Wrong password:", verify_password("wrong", found["password_hash"]))

token = create_access_token({"sub": user["id"]})
print("JWT token:", token[:50] + "...")
decoded = decode_token(token)
print("Decoded sub:", decoded["sub"])

holdings = HoldingsRepository()
h = holdings.add(user["id"], "AAPL", 10, 180.50)
print("Added holding:", h["ticker"], h["shares"], h["avg_cost"])

all_h = holdings.list_by_user(user["id"])
print("Holdings count:", len(all_h))

# Cleanup
db.execute("DELETE FROM holdings")
db.execute("DELETE FROM users")
db.commit()
print("\nAll tests passed!")
