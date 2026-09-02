import pytest
from fastapi.testclient import TestClient
from app.main import app
from generate_sample_excel import generate_sample_excel

client = TestClient(app)

def test_api_flow(tmp_path):
    excel_path = tmp_path / "test_data.xlsx"
    generate_sample_excel(str(excel_path))

    with open(excel_path, "rb") as f:
        response = client.post("/api/upload", files={"file": ("test_data.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    
    assert response.status_code == 201
    json_res = response.json()
    assert "upload_id" in json_res
    assert "sucesso" in json_res["message"].lower() or "success" in json_res["message"].lower()
    upload_id = json_res["upload_id"]

    assert json_res["records_ingested"]["debt_control"] == 2
    assert json_res["records_ingested"]["financial_investment"] == 9
    assert json_res["records_ingested"]["real_estate"] == 3
    assert json_res["records_ingested"]["livestock_inventory"] == 2
    assert json_res["records_ingested"]["vehicle_fleet"] == 2

    resp = client.get("/api/uploads")
    assert resp.status_code == 200
    uploads = resp.json()
    assert len(uploads) >= 1
    assert uploads[0]["id"] == upload_id

    resp = client.get(f"/api/debts?upload_id={upload_id}&sort_order=asc")
    assert resp.status_code == 200
    debts = resp.json()
    assert len(debts) == 2
    assert float(debts[0]["initial_balance"]) == 1000000.0

    resp = client.get(f"/api/investments?upload_id={upload_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 9

    resp = client.get(f"/api/real-estate?upload_id={upload_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 3

    resp = client.get(f"/api/livestock?upload_id={upload_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = client.get(f"/api/vehicles?upload_id={upload_id}")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = client.get(f"/api/dashboard/summary?upload_id={upload_id}")
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["upload_id"] == upload_id
    assert float(summary["total_real_estate"]) == 22500000.0
    assert float(summary["total_vehicles"]) == 670000.0
    assert float(summary["total_livestock"]) == 3869345.0

    del_resp = client.delete(f"/api/upload/{upload_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_upload_id"] == upload_id

    get_del = client.get(f"/api/debts?upload_id={upload_id}")
    assert len(get_del.json()) == 0

def test_consolidated_livestock_flow():
    import os
    from pathlib import Path
    sample_v2 = Path(r"C:\Users\brenosouza-nmb\Downloads") / "Modelo Relatório Semanal Zé v2.xlsx"
    if not sample_v2.exists():
        return

    with open(sample_v2, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("Modelo Relatório Semanal Zé v2.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    assert response.status_code == 201
    res_data = response.json()
    upload_id = res_data["upload_id"]
    assert res_data["records_ingested"]["livestock_inventory"] == 5

    summary_resp = client.get(f"/api/livestock/summary?upload_id={upload_id}")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["has_consolidated_summary"] is True
    assert summary["total_cabecas"] == 51219
    assert float(summary["valor_rebanho"]) == 250057478.45
    assert float(summary["frete_total"]) == 3892321.27
    assert float(summary["comissao_total"]) == 921002.27
    assert float(summary["investimento_total"]) == 254870801.98
    assert float(summary["valor_medio_cabeca"]) == 4882.12
    assert float(summary["peso_medio_cabeca"]) == 365.77

    assert len(summary["distribuicao_local"]) == 2
    assert summary["distribuicao_local"][0]["local"] == "Confinamento"
    assert summary["distribuicao_local"][0]["cabecas"] == 36592

    assert len(summary["distribuicao_uf"]) == 3
    assert summary["distribuicao_uf"][0]["uf"] == "MT"
    assert summary["distribuicao_uf"][0]["cabecas"] == 31668

    assert len(summary["distribuicao_operador"]) == 5
    assert summary["distribuicao_operador"][0]["operador"] == "Tripoloni"
    assert summary["distribuicao_operador"][0]["cabecas"] == 22786

    dash_resp = client.get(f"/api/dashboard/summary?upload_id={upload_id}")
    assert dash_resp.status_code == 200
    dash = dash_resp.json()
    assert float(dash["total_livestock"]) == 254870801.98

    del_resp = client.delete(f"/api/upload/{upload_id}")
    assert del_resp.status_code == 200


