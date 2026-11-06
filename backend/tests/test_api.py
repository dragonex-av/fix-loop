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

def test_customer_history_timeline():
    # Rahul is customer #1
    response = client.get("/api/customers/1/history")
    assert response.status_code == 200
    data = response.json()
    assert data["customer"]["name"] == "Rahul Sharma"
    assert len(data["timeline"]) >= 2
    # Verify events exist
    types = [t["type"] for t in data["timeline"]]
    assert "ticket_created" in types
    assert "repair_performed" in types

def test_ai_repair_assistant():
    # Analyze ticket 1 (Rahul's initial complaint)
    response = client.post("/api/tickets/1/analyze")
    assert response.status_code == 200
    data = response.json()
    assert "repeat_issue" in data
    assert "suggested_inspection_areas" in data
    assert len(data["suggested_inspection_areas"]) > 0
    assert "supporting_evidence" in data

def test_ripple_effect_patterns():
    response = client.get("/api/insights/patterns")
    assert response.status_code == 200
    patterns = response.json()
    assert len(patterns) >= 1
    # Check Model X drainage cluster
    p = patterns[0]
    assert p["product_model"] == "Model X"
    assert p["issue_category"] == "Drainage issue"
    assert p["case_count"] >= 3
    assert len(p["supporting_cases"]) >= 3

def test_followup_center():
    response = client.get("/api/followups")
    assert response.status_code == 200
    followups = response.json()
    assert len(followups) >= 2
    statuses = [f["status"] for f in followups]
    assert "overdue" in statuses

def test_memory_explorer_events():
    response = client.get("/api/memory/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    assert events[0]["operation"] in ["retain", "recall"]
