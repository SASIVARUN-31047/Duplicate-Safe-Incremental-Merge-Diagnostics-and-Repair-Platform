from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_seed_and_kpis():
    # 1. Seed data
    response = client.post("/api/seed")
    assert response.status_code == 200
    
    # 2. Check KPIs
    kpi_resp = client.get("/api/kpis")
    assert kpi_resp.status_code == 200
    data = kpi_resp.json()
    assert data["total_rows_processed"] > 0
    assert data["duplicates_detected"] == 4
    
    # 3. Check duplicates
    dups_resp = client.get("/api/duplicates")
    assert dups_resp.status_code == 200
    dups = dups_resp.json()
    assert len(dups) == 4
    
    # 4. Find the QUARANTINED one to resolve
    q_flag = next((d for d in dups if d["decision_status"] == "PENDING_REVIEW"), None)
    assert q_flag is not None
    
    # 5. Resolve quarantine
    decision_id = q_flag["decision_id"]
    res_resp = client.post(f"/api/quarantine/{decision_id}/resolve", json={"action": "APPROVE_INCOMING"})
    assert res_resp.status_code == 200
    
    # 6. Check root cause
    rc_resp = client.get(f"/api/duplicates/{q_flag['id']}/root-cause")
    assert rc_resp.status_code == 200
    rc_data = rc_resp.json()
    assert rc_data["decision"]["status"] == "MANUALLY_APPROVED"

