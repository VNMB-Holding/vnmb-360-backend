import io
import pytest
import pandas as pd
from app.services.excel_parser import ExcelParserService, clean_numeric, parse_date
from generate_sample_excel import generate_sample_excel

def test_clean_numeric():
    assert clean_numeric("1.500,50") == 1500.50
    assert clean_numeric("R$ 250.000,00") == 250000.00
    assert clean_numeric("10.5%") == 10.5
    assert clean_numeric(None) is None
    assert clean_numeric("Total") is None

def test_parse_date():
    assert parse_date("01/12/2025").strftime("%Y-%m-%d") == "2025-12-01"
    assert parse_date("2026-08-11").strftime("%Y-%m-%d") == "2026-08-11"
    assert parse_date("12/2025").strftime("%Y-%m-%d") == "2025-12-01"
    assert parse_date(None) is None

def test_excel_parser_with_sample_file(tmp_path):
    excel_path = tmp_path / "sample.xlsx"
    generate_sample_excel(str(excel_path))

    with open(excel_path, "rb") as f:
        content = f.read()

    data = ExcelParserService.parse_excel(content)

    assert "debt_control" in data
    assert len(data["debt_control"]) == 2
    assert data["debt_control"][0]["initial_balance"] == 1000000.00

    assert "financial_investment" in data
    # 3 assets x 3 date columns = 9 records
    assert len(data["financial_investment"]) == 9

    assert "real_estate" in data
    assert len(data["real_estate"]) == 3
    assert data["real_estate"][0]["description"] == "Fazenda Bela Vista"
    assert data["real_estate"][0]["market_value"] == 15000000.00

    assert "livestock_inventory" in data
    assert len(data["livestock_inventory"]) == 2

    assert "vehicle_fleet" in data
    assert len(data["vehicle_fleet"]) == 2
