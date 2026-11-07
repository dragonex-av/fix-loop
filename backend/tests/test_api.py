import pytest
from datetime import datetime, timezone, timedelta
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
    # Test Employee (Admin) Login
    resp_emp = client.post("/api/auth/login", json={"email": "admin@fixloop.com", "password": "password123"})
    assert resp_emp.status_code == 200
    data_emp = resp_emp.json()
    assert data_emp["user"]["role"].upper() == "ADMIN"
    assert "access_token" in data_emp
    assert "refresh_token" in data_emp

    # Test Customer Login
    resp_cust = client.post("/api/auth/login", json={"email": "rahul@example.com", "password": "password123"})
    assert resp_cust.status_code == 200
    data_cust = resp_cust.json()
    assert data_cust["user"]["role"].upper() == "CUSTOMER"
    assert "access_token" in data_cust

def test_google_login_mock():
    # Test Google Login for customer
    resp = client.post("/api/auth/google", json={"id_token": "mock-google-token-googlecustomer@gmail.com", "target_role": "CUSTOMER"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == "googlecustomer@gmail.com"
    assert data["user"]["role"] == "CUSTOMER"
    assert "access_token" in data

    # Test Google Login cannot self-promote to ADMIN
    resp_hacker = client.post("/api/auth/google", json={"id_token": "mock-google-token-hacker@gmail.com", "target_role": "ADMIN"})
    assert resp_hacker.status_code == 200
    # Must remain CUSTOMER because hacker@gmail.com is not in ADMIN_EMAILS
    assert resp_hacker.json()["user"]["role"] == "CUSTOMER"

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
        detail = client.get(f"/api/portal/tickets/{t['id']}", headers=headers)
        assert detail.status_code == 200

    # Test accessing a ticket that doesn't belong to Rahul (TCK-1003 belongs to Priya)
    resp_forbidden = client.get("/api/portal/tickets/3", headers=headers)
    assert resp_forbidden.status_code == 404

def test_technicians_and_operations():
    # Login as Admin/Staff
    resp_exec = client.post("/api/auth/login", json={"email": "admin@fixloop.com", "password": "password123"})
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
    resp_admin = client.post("/api/auth/login", json={"email": "admin@fixloop.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {resp_admin.json()['access_token']}"}
    response = client.post("/api/tickets/1/analyze", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "repeat_issue" in data
    assert "suggested_inspection_areas" in data
    assert len(data["suggested_inspection_areas"]) > 0

def test_ripple_effect_patterns():
    resp_admin = client.post("/api/auth/login", json={"email": "admin@fixloop.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {resp_admin.json()['access_token']}"}
    response = client.get("/api/insights/patterns", headers=headers)
    assert response.status_code == 200
    patterns = response.json()
    assert len(patterns) >= 1
    p = patterns[0]
    assert p["product_model"] == "Model X"
    assert p["issue_category"] == "Drainage issue"
    assert p["case_count"] >= 3

def test_repeat_detection_and_classification():
    # 1. Classification rule-based check
    from app.services.classifier_service import classify_issue_rule_based
    assert classify_issue_rule_based("E20 error standing water") == "Drainage issue"
    assert classify_issue_rule_based("fresh food compartment warm not cooling") == "Cooling issue"
    assert classify_issue_rule_based("loud humming noise from drum spin") == "Spin & Motor issue"
    assert classify_issue_rule_based("dead no power switch not turning on") == "Power & Electrical issue"

    # 2. Seeded TCK-1010 repeat check
    resp_admin = client.post("/api/auth/login", json={"email": "admin@fixloop.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {resp_admin.json()['access_token']}"}
    res_t10 = client.get("/api/tickets/9", headers=headers)
    assert res_t10.status_code == 200
    ticket10 = res_t10.json()
    assert ticket10["ticket_code"] == "TCK-1010"
    assert ticket10["is_repeat"] is True

def test_state_machine_and_scheduling():
    resp_admin = client.post("/api/auth/login", json={"email": "admin@fixloop.com", "password": "password123"})
    admin_headers = {"Authorization": f"Bearer {resp_admin.json()['access_token']}"}

    # Ticket 4 (TCK-1004) is in OPEN status
    # 1. Illegal move: OPEN -> RESOLVED must return 409
    resp_illegal = client.post("/api/tickets/4/start-work", json={}, headers=admin_headers)
    assert resp_illegal.status_code == 409

    # 2. Valid move: OPEN -> SCHEDULED with appointment
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    resp_sched = client.post(
        "/api/tickets/4/schedule",
        json={"technician_id": 1, "scheduled_at": future_time, "notes": "Morning arrival"},
        headers=admin_headers
    )
    assert resp_sched.status_code == 200
    assert resp_sched.json()["status"] == "SCHEDULED"

    # 3. Double-booking conflict check: scheduling tech 1 at the exact same hour must return 409
    resp_conflict = client.post(
        "/api/tickets/6/schedule",
        json={"technician_id": 1, "scheduled_at": future_time, "notes": "Conflict test"},
        headers=admin_headers
    )
    assert resp_conflict.status_code == 409
    assert "already booked" in resp_conflict.json()["detail"]

def test_two_step_otp_resolution_and_retain():
    resp_admin = client.post("/api/auth/login", json={"email": "admin@fixloop.com", "password": "password123"})
    admin_headers = {"Authorization": f"Bearer {resp_admin.json()['access_token']}"}

    resp_priya = client.post("/api/auth/login", json={"email": "priya@example.com", "password": "password123"})
    priya_headers = {"Authorization": f"Bearer {resp_priya.json()['access_token']}"}

    # Ticket 3 (TCK-1003) belongs to Priya and is IN_PROGRESS
    # 1. Technician marks as solved -> PENDING_VERIFICATION
    resp_req = client.post("/api/tickets/3/request-resolution", headers=admin_headers)
    assert resp_req.status_code == 200
    assert resp_req.json()["status"] == "PENDING_VERIFICATION"

    # 2. Check that Priya (Customer) received the OTP in notification/detail
    resp_detail = client.get("/api/portal/tickets/3", headers=priya_headers)
    assert resp_detail.status_code == 200
    otp = resp_detail.json()["customer_otp"]
    assert otp is not None
    assert len(otp) == 6

    # 3. Test wrong OTP attempt
    resp_wrong = client.post("/api/tickets/3/verify-resolution", json={"code": "000000"}, headers=admin_headers)
    assert resp_wrong.status_code == 400
    assert "Incorrect" in resp_wrong.json()["detail"]

    # 4. Correct OTP verification -> RESOLVED
    resp_verify = client.post("/api/tickets/3/verify-resolution", json={"code": otp}, headers=admin_headers)
    assert resp_verify.status_code == 200
    assert resp_verify.json()["status"] == "RESOLVED"

    # 5. OTP cannot be reused
    resp_reuse = client.post("/api/tickets/3/verify-resolution", json={"code": otp}, headers=admin_headers)
    assert resp_reuse.status_code == 400

    # 6. Verify notification created for both
    notifs = client.get("/api/notifications", headers=priya_headers).json()
    assert any(n["type"] == "TICKET_RESOLVED" for n in notifs)

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
