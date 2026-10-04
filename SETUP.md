# Setup Guide

## Option A - Docker (recommended)
1. Install Docker Desktop and make sure it is running.
2. In a terminal:
   ```bash
   cd smart-logistics-predictor
   cp .env.example .env          # Windows PowerShell: Copy-Item .env.example .env
   docker compose up --build
   ```
3. Wait until the log shows the backend is healthy (about 1-2 minutes the first time), then open http://localhost:5173.
4. Login: `admin@logistics.local` / `Admin@123`.

Stop: `Ctrl+C`, then `docker compose down`. Reset all data: `docker compose down -v`.

**Ports used:** 5173 (frontend), 8000 (backend), 5433 (PostgreSQL on your machine). If a port is busy, change it in `docker-compose.yml`.
If you change the backend port, also set `VITE_API_URL` (and `CORS_ORIGINS` if you change the frontend port) in `.env`.

### Troubleshooting
| Problem | Fix |
|---|---|
| Frontend shows "Cannot reach the server" | Backend not ready yet, or `VITE_API_URL` wrong. Rebuild after changing it: `docker compose up --build` |
| Login works in Swagger but not in the UI | CORS: make sure `CORS_ORIGINS` contains the exact URL you use in the browser |
| Port already in use | Change the left side of the port mapping in `docker-compose.yml` |
| Old data keeps appearing | `docker compose down -v` removes the database volume |

## Option B - Local without Docker
### 1. Backend
```bash
cd smart-logistics-predictor
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r backend/requirements-dev.txt
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
With no `DATABASE_URL` set, a local SQLite file (`backend/logistics_dev.db`) is used - fine for a quick demo.

**To use PostgreSQL locally**, create a database named `logistics`, then set (before starting the backend):
```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/logistics     # Windows: set DATABASE_URL=...
```
### 2. Frontend (second terminal)
```bash
cd smart-logistics-predictor/frontend
npm install
npm run dev
```
Open http://localhost:5173.

## Retrain the model (optional)
```bash
python ml/generate_dataset.py
python ml/train_model.py
```
Restart the backend afterwards so it loads the new `models/eta_model.joblib`.

## Run the tests
```bash
cd backend && python -m pytest -v
cd ../frontend && npm test
```

## Changing risk thresholds
Set environment variables (in `.env`) and restart the backend, for example `RISK_HIGH_RATIO=1.25`. Defaults: MEDIUM when
predicted > 1.00 x promised, HIGH when predicted > 1.15 x promised. See `backend/app/config.py`.
