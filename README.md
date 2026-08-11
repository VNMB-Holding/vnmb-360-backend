# Wealth & Asset Consolidation Backend API

A production-ready Python + FastAPI backend for ingesting complex wealth consolidation Excel files, parsing and transforming multi-sheet financial data using Pandas, persisting entities into a relational database (PostgreSQL / SQLite) via SQLAlchemy, and serving RESTful endpoints for dashboard consumption.

---

## Features

- **Clean Architecture**: Separated endpoints, Pydantic schemas (DTOs), SQLAlchemy models, and service layer.
- **Robust Excel Parser (`Pandas` + `openpyxl`)**:
  - Custom sheet offset rules (`skiprows`) for ignoring visual headers.
  - Automatic column mapping (Portuguese to English).
  - Unpivots dynamic monthly investment columns into normalized date records.
  - Cleans Brazilian currency formatting, percentages, and drops `Unnamed` columns & summary total rows.
- **Full Database Coverage**:
  - `DebtControl` (`debt_control`)
  - `FinancialInvestment` (`financial_investment`)
  - `RealEstate` (`real_estate`)
  - `LivestockInventory` (`livestock_inventory`)
  - `VehicleFleet` (`vehicle_fleet`)
- **Automated Verification & Tests**: Includes sample Excel generator (`generate_sample_excel.py`) and pytest suite (`pytest`).

---

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Data Processing:** Pandas, OpenPyXL
- **ORM:** SQLAlchemy 2.0
- **Database:** PostgreSQL (with SQLite zero-config fallback)
- **Validation:** Pydantic v2
- **Testing:** Pytest & HTTPX

---

## Project Structure

```
vnmb-360-backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── upload.py        # POST /api/upload & POST /api/upload-excel
│   │   │   ├── debts.py         # GET /api/debts (with sorting)
│   │   │   ├── investments.py   # GET /api/investments (with date filter)
│   │   │   ├── real_estate.py   # GET /api/real-estate
│   │   │   ├── livestock.py     # GET /api/livestock
│   │   │   ├── vehicles.py      # GET /api/vehicles
│   │   │   └── dashboard.py     # GET /api/dashboard/summary
│   │   ├── router.py            # API router compilation
│   │   └── __init__.py
│   ├── config.py                # Environment configuration
│   ├── db/
│   │   ├── base.py              # Declarative base
│   │   └── session.py           # Engine & SessionLocal setup
│   ├── models/                  # SQLAlchemy ORM Models
│   │   ├── debt.py
│   │   ├── investment.py
│   │   ├── real_estate.py
│   │   ├── livestock.py
│   │   ├── vehicle.py
│   │   └── __init__.py
│   ├── schemas/                 # Pydantic Schemas / DTOs
│   │   ├── debt.py
│   │   ├── investment.py
│   │   ├── real_estate.py
│   │   ├── livestock.py
│   │   ├── vehicle.py
│   │   ├── summary.py
│   │   └── __init__.py
│   ├── services/
│   │   ├── excel_parser.py      # Excel parsing & unpivot logic
│   │   ├── dashboard.py         # Net worth calculation logic
│   │   └── __init__.py
│   ├── __init__.py
│   └── main.py                  # FastAPI application entry point
├── tests/
│   ├── test_excel_parser.py     # Parser unit tests
│   └── test_api.py              # Endpoint integration tests
├── generate_sample_excel.py      # Utility script creating sample data
├── requirements.txt             # Project dependencies
├── .env.example                 # Environment variable template
└── README.md
```

---

## Quick Start Guide

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*Note: By default, `sqlite:///./wealth_360.db` is used for out-of-the-box local development. To use PostgreSQL, set `DATABASE_URL=postgresql://user:password@localhost:5432/wealth_db` in `.env`.*

### 4. Generate Sample Excel File
Run the sample data generator to create `sample_wealth_data.xlsx`:
```bash
python generate_sample_excel.py
```

### 5. Run the Server
Start the development server with Uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```
Open your browser at [http://localhost:8000/docs](http://localhost:8000/docs) to view the Interactive OpenAPI Documentation.

---

## API Documentation

### Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Ingests `.xlsx` file, parses sheets, resets database tables, and inserts parsed entities. |
| `POST` | `/api/upload-excel` | Alias endpoint for file upload. |
| `GET` | `/api/debts` | Fetch debt history. Query Param: `sort_order` (`asc` / `desc`). |
| `GET` | `/api/investments` | Fetch investments. Query Param: `reference_date` (`YYYY-MM-DD`). |
| `GET` | `/api/real-estate` | Fetch real estate properties list. |
| `GET` | `/api/livestock` | Fetch livestock inventory. |
| `GET | `/api/vehicles` | Fetch vehicle fleet. |
| `GET` | `/api/dashboard/summary` | Returns aggregated net worth (Real Estate + Vehicles + Livestock + Investments [latest] - Debts [latest]). |

---

## Running Automated Tests

Run the test suite with `pytest`:
```bash
pytest -v
```
