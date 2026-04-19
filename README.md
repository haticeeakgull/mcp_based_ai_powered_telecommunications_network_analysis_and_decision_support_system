# MCP Based AI Powered Telecommunications Network Analysis and Decision Support System

This project provides a telecom NOC-oriented architecture with:
- synthetic data generation,
- offline anomaly detection pipeline,
- MCP tools for AI agents,
- FastAPI endpoints for dashboard/backend use.

## 1) Project Goal

The system helps answer operational questions such as:
- Is there an anomaly in a specific cell?
- Which region has open faults?
- Are complaints increasing in a region?
- What is the latest KPI state of a cell?

It combines:
- `network_metrics` (performance),
- `anomaly_results` (precomputed anomaly output),
- `faults`,
- `complaints`,
- `base_stations`.

## 2) Important Files

- `main.py`
  - Runs MCP tools (`--mode mcp`)
  - Runs FastAPI app (`--mode api`)
- `anamoly_detector.py`
  - Offline anomaly pipeline (Isolation Forest + Z-Score)
  - Writes to `anomaly_results`
- `database/`
  - Data generation scripts for metrics/faults/complaints
- `.env`
  - Local secrets and DB config (not committed)
- `.env.example`
  - Safe template for teammates

## 3) Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

## 4) Environment Variables

Copy `.env.example` to `.env` and fill values:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=network_mcp
DB_USER=postgres
DB_PASSWORD=your_password
```

## 5) Run Modes

### A) MCP mode (for MCP Inspector / LLM agent calls)

```bash
python main.py --mode mcp
```

### B) API mode (for REST testing / integration)

```bash
python main.py --mode api --host 127.0.0.1 --port 8000
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

## 6) MCP Tools

Current tool set:

1. `get_metrics(cell_id, slice_type=None, since=None, limit=10)`
2. `get_anomalies(cell_id=None, severity=None, only_anomalies=True, limit=50)`
3. `get_faults(cell_id=None, region=None, resolved=None, limit=50)`
4. `get_complaints(cell_id=None, region=None, since=None, limit=50)`
5. `get_station(cell_id=None, region=None, status=None, limit=50)`

## 7) FastAPI Endpoints

- `GET /health`
- `GET /metrics`
- `GET /anomalies`
- `GET /faults`
- `GET /complaints`
- `GET /stations`

## 8) Data + Anomaly Pipeline Flow

Recommended demo workflow:

1. Generate/load seed data into PostgreSQL (`network_metrics`, `faults`, `complaints`, `base_stations`).
2. Run anomaly pipeline once:

```bash
python anamoly_detector.py --mode full
```

3. Start MCP:

```bash
python main.py --mode mcp
```

4. Test tools in MCP Inspector.

## 9) Demo Queries (Quick Start)

Examples:

- Metrics (normal check):
  - `cell_id=CELL_017`, `limit=10`
- Anomalies (cell):
  - `cell_id=CELL_017`, `only_anomalies=true`
- Faults (region open faults):
  - `region=Buca`, `resolved=false`
- Complaints (region):
  - `region=Konak`, `limit=30`
- Station:
  - `cell_id=CELL_017`

## 10) Security Notes

- Never commit real secrets.
- Keep `.env` in `.gitignore`.
- Use credential rotation if any secret is exposed.

## 11) Troubleshooting

- `ModuleNotFoundError`: run `pip install -r requirements.txt`
- Empty responses from tools:
  - verify table data exists,
  - verify region/cell names,
  - verify anomaly pipeline was executed (`anomaly_results` populated).

## 12) Team Notes

- Offline detection (`anamoly_detector.py`) and online tool serving (`main.py`) are intentionally separated.
- MCP tools should read prepared analysis outputs (`anomaly_results`) instead of retraining model on every call.
