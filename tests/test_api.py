import pytest
from fastapi.testclient import TestClient
from app.main import app
from generate_sample_excel import generate_sample_excel

client = TestClient(app)

def test_api_flow(tmp_path):
    # 1. Generate sample Excel
    excel_path = tmp_path / "test_data.xlsx"
    generate_sample_excel(str(excel_path))

    # 2. Upload file via POST /api/upload
    with open(excel_path, "rb") as f:
        response = client.post("/api/upload", files={"file": ("test_data.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    
    assert response.status_code == 201
    json_res = response.json()
    assert json_res["message"] == "Excel file uploaded and data successfully ingested into history batch."
    assert "upload_id" in json_res
    upload_id = json_res["upload_id"]

    assert json_res["records_ingested"]["debt_control"] == 2
    assert json_res["records_ingested"]["financial_investment"] == 9
    assert json_res["records_ingested"]["real_estate"] == 3
    assert json_res["records_ingested"]["livestock_inventory"] == 2
    assert json_res["records_ingested"]["vehicle_fleet"] == 2

    # 3. Test GET /api/uploads
    resp = client.get("/api/uploads")
    assert resp.status_code == 200
    uploads = resp.json()
    assert len(uploads) >= 1
    assert uploads[0]["id"] == upload_id

    # 4. Test GET /api/debts
    resp = client.get(f"/api/debts?upload_id={upload_id}&sort_order=asc")
    assert resp.status_code == 200
    debts = resp.json()
    assert len(debts) == 2
    assert float(debts[0]["initial_balance"]) == 1000000.0

    # 5. Test GET /api/investments
    resp = client.get(f"/api/investments?upload_id={upload_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 9

    # 6. Test GET /api/real-estate
    resp = client.get(f"/api/real-estate?upload_id={upload_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 3

    # 7. Test GET /api/livestock
    resp = client.get(f"/api/livestock?upload_id={upload_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    # 8. Test GET /api/vehicles
    resp = client.get(f"/api/vehicles?upload_id={upload_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    # 9. Test GET /api/dashboard/summary
    resp = client.get(f"/api/dashboard/summary?upload_id={upload_id}")
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["upload_id"] == upload_id
    assert float(summary["total_real_estate"]) == 22500000.0
    assert float(summary["total_vehicles"]) == 670000.0
    assert float(summary["total_livestock"]) == 3869345.0

    # 10. Test DELETE /api/upload/{upload_id}
    del_resp = client.delete(f"/api/upload/{upload_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_upload_id"] == upload_id

    # Verify deleted
    get_del = client.get(f"/api/debts?upload_id={upload_id}")
    assert len(get_del.json()) == 0
