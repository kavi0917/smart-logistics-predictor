# Smart Logistics Delivery Prediction System

**Improving On-Time Delivery Predictability in Logistics** - MCA Design Thinking project (23CAP320, Assignment II).
Author: Kavipriyadharsan P (Roll No. 717825Z129), Karpagam College of Engineering.

A web application that helps logistics managers predict whether shipments will arrive on time. It predicts the delivery
time (ETA) with a machine-learning model, classifies each shipment as **LOW / MEDIUM / HIGH** delay risk, explains *why*,
raises alerts for high-risk shipments, stores prediction history and compares predictions with what actually happened.

> **This is an academic prototype.** The ML model is trained on a *synthetic* dataset (see `ml/README.md`). Results show that the
> pipeline works end to end; they are not evidence of real-world accuracy.

## Features
- Dashboard with 8 KPI cards and 5 charts, all calculated from the database
- Shipment CRUD (create / view / edit / delete) with search and filters; a prediction is generated automatically on save
- ETA prediction (`RandomForestRegressor` inside a scikit-learn `Pipeline`) + rule-based risk layer with configurable thresholds
- Human-readable risk reasons (high traffic, rain, long distance, warehouse delay, previous route delay, peak hour, route history)
- Alerts for HIGH-risk active shipments (read/unread)
- Prediction history with error = `ABS(actual - predicted)` once actual delivery is known
- Analytics: summary, risk distribution, performance over time, prediction accuracy (MAE, RMSE, within-15-min %)
- What-If simulation: re-runs the model with changed traffic / weather / vehicle / delays (nothing hard-coded)
- JWT login, bcrypt password hashing, Pydantic validation, CORS config, no secrets in Git
- Docker Compose, 48 automated tests (36 backend/ML + 12 frontend), GitHub Actions CI/CD

## Architecture
```
React (Vite) --REST/JSON--> FastAPI --SQLAlchemy--> PostgreSQL
                               |
                               +--> ML prediction service --> eta_model.joblib (preprocessing + RandomForest)
                                         |
                                         +--> risk layer (thresholds from config) --> risk level, probability, reasons
```
Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Technology stack
React 18, Vite, Recharts, Axios | Python 3.12, FastAPI, Pydantic, SQLAlchemy | PostgreSQL 16 |
pandas, NumPy, scikit-learn, joblib | Docker, Docker Compose | GitHub Actions | pytest, Vitest

## Requirements
- **Easiest:** Docker Desktop (Compose v2). Nothing else needed.
- **Without Docker:** Python 3.12+, Node.js 20+ (22 recommended), optionally PostgreSQL 16 (SQLite is used if no `DATABASE_URL`).

## Quick start (Docker)
```bash
cd smart-logistics-predictor
cp .env.example .env
docker compose up --build
```
| What | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

**Demo login:** `admin@logistics.local` / `Admin@123` (local demo account only).
On first start the backend creates the tables, the demo user, 63 sample shipments, their prediction history and the alerts.

## Local setup (no Docker)
See [SETUP.md](SETUP.md) for step-by-step commands (backend, frontend, PostgreSQL or SQLite).

## Database setup
Tables: `users`, `shipments`, `prediction_history`, `alerts`. Created automatically at startup.
Manual seeding / reset: `python scripts/seed_database.py [--reset]`.

## ML training
```bash
pip install -r backend/requirements.txt
python ml/generate_dataset.py   # writes data/logistics_delivery_data.csv (2,500 synthetic rows)
python ml/train_model.py        # prints MAE / RMSE / R2, saves models/eta_model.joblib
python ml/evaluate_model.py     # evaluates on the held-out test split + feature importances
```
The repository already contains a trained model, so retraining is optional.

## Run backend / frontend manually
```bash
# backend (from backend/)
python -m uvicorn app.main:app --reload --port 8000
# frontend (from frontend/)
npm install && npm run dev        # http://localhost:5173
```
The frontend reads the API address from `VITE_API_URL` (default `http://localhost:8000`).

## API documentation
Interactive: http://localhost:8000/docs. Written reference: [docs/API.md](docs/API.md).

## Testing
```bash
cd backend && pip install -r requirements-dev.txt && python -m pytest -v    # 36 tests
cd frontend && npm test                                                     # 12 tests
```

## CI/CD
`.github/workflows/ci.yml` (every push/PR): train model -> backend tests -> frontend tests + build -> Docker build + smoke test.
`.github/workflows/cd.yml` publishes images to GitHub Container Registry on version tags. See [docs/CICD.md](docs/CICD.md).

## Documentation map
[SETUP.md](SETUP.md) | [PROJECT_REPORT.md](PROJECT_REPORT.md) | [DEMO_GUIDE.md](DEMO_GUIDE.md) | `docs/` (architecture, API, design thinking, scrum plan, CI/CD, DevOps)

## Screenshots
Add your own after running the app (suggested names):
`docs/screenshots/dashboard.png`, `shipments.png`, `shipment-detail.png`, `alerts.png`, `analytics.png`, `what-if.png`.

## Known limitations
- Synthetic training data; the model has never seen real shipments.
- `delay_probability` is a heuristic score derived from predicted vs promised time, **not** a calibrated probability.
- The model does not use live traffic/weather feeds, road closures or GPS; conditions are entered manually.
- Basic single-role authentication; the JWT is stored in browser `localStorage` (acceptable for a prototype, not for production).
- No SMS/e-mail alerts (dashboard notifications only).

## Future improvements
Real traffic/weather APIs, model retraining on real data, probability calibration, role-based access, e-mail/WhatsApp alerts,
Kubernetes deployment, Prometheus/Grafana monitoring.
