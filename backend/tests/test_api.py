import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "FixLoop" in data["app"]

def test_dashboard():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tickets"] >= 8
    assert data["active_patterns"] >= 1
    assert data["overdue_followups"] >= 1

def test_auth_login_and_roles():
    # Test Employee Login
    resp_emp = client.post("/api/auth/login", json={"email": "admin@fixloop.com", "password": "password123"})
    assert resp_emp.status_code == 200
    data_emp = resp_emp.json()
    assert data_emp["user"]["role"] == "admin"
    assert "access_token" in data_emp

    # Test Customer Login
    resp_cust = client.post("/api/auth/login", json={"email": "rahul@example.com", "password": "password123"})
    assert resp_cust.status_code == 200
    data_cust = resp_cust.json()
    assert data_cust["user"]["role"] == "customer"
    assert "access_token" in data_cust

def test_customer_portal_isolation():
    # Login as Rahul
    resp_rahul = client.post("/api/auth/login", json={"email": "rahul@example.com", "password": "password123"})
    token_rahul = resp_rahul.json()["access_token"]
    headers = {"Authorization": f"Bearer {token_rahul}"}

    # Fetch Rahul's tickets
    resp_tickets = client.get("/api/portal/my-tickets", headers=headers)
    assert resp_tickets.status_code == 200
    data = resp_tickets.json()
    assert data["customer"]["name"] == "Rahul Sharma"
    # Ensure all returned tickets belong ONLY to Rahul
    for t in data["active_repairs"] + data["past_services"]:
        # Detail lookup
        detail = client.get(f"/api/portal/tickets/{t['id']}", headers=headers)
        assert detail.status_code == 200

    # Test accessing a ticket that doesn't belong to Rahul (e.g. ticket 3 which belongs to Priya)
    resp_forbidden = client.get("/api/portal/tickets/3", headers=headers)
    assert resp_forbidden.status_code == 404

def test_technicians_and_operations():
    # Login as Support Executive
    resp_exec = client.post("/api/auth/login", json={"email": "support@fixloop.com", "password": "password123"})
    token_exec = resp_exec.json()["access_token"]
    headers = {"Authorization": f"Bearer {token_exec}"}

    resp_techs = client.get("/api/operations/technicians", headers=headers)
    assert resp_techs.status_code == 200
    techs = resp_techs.json()
    assert len(techs) >= 2
    tech_names = [t["name"] for t in techs]
    assert "Vikram Singh" in tech_names

    # Customer trying to access employee route must be 403 Forbidden
    resp_cust = client.post("/api/auth/login", json={"email": "rahul@example.com", "password": "password123"})
    token_cust = resp_cust.json()["access_token"]
    headers_cust = {"Authorization": f"Bearer {token_cust}"}
    resp_denied = client.get("/api/operations/technicians", headers=headers_cust)
    assert resp_denied.status_code == 403

def test_customer_history_timeline():
    response = client.get("/api/customers/1/history")
    assert response.status_code == 200
    data = response.json()
    assert data["customer"]["name"] == "Rahul Sharma"
    assert len(data["timeline"]) >= 2

def test_ai_repair_assistant():
    response = client.post("/api/tickets/1/analyze")
    assert response.status_code == 200
    data = response.json()
    assert "repeat_issue" in data
    assert "suggested_inspection_areas" in data
    assert len(data["suggested_inspection_areas"]) > 0

def test_ripple_effect_patterns():
    response = client.get("/api/insights/patterns")
    assert response.status_code == 200
    patterns = response.json()
    assert len(patterns) >= 1
    p = patterns[0]
    assert p["product_model"] == "Model X"
    assert p["issue_category"] == "Drainage issue"
    assert p["case_count"] >= 3

def test_followup_center():
    response = client.get("/api/followups")
    assert response.status_code == 200
    followups = response.json()
    assert len(followups) >= 1

def test_memory_explorer_events():
    response = client.get("/api/memory/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
