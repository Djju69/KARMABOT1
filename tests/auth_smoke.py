import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from web.main import app

# Unsigned JWT accepted by fallback for roles partner/admin/superadmin
TOKEN = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIiwicm9sZSI6InBhcnRuZXIifQ.x"

client = TestClient(app)

def show(label, resp):
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    print(f"{label}: {resp.status_code} -> {str(body)[:500]}")

# Health
r = client.get("/health")
show("/health", r)

# Profile with header
r = client.get("/cabinet/profile", headers={"Authorization": f"Bearer {TOKEN}"})
show("/cabinet/profile (hdr)", r)

# Profile with query token
r = client.get(f"/cabinet/profile?token={TOKEN}")
show("/cabinet/profile (?token)", r)

# Cards with header
r = client.get("/cabinet/partner/cards?limit=20", headers={"Authorization": f"Bearer {TOKEN}"})
show("/cabinet/partner/cards (hdr)", r)

# Cards with query token
r = client.get(f"/cabinet/partner/cards?limit=20&token={TOKEN}")
show("/cabinet/partner/cards (?token)", r)
