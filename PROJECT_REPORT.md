# Smart Logistics Delivery Prediction System
## Improving On-Time Delivery Predictability in Logistics

**Course:** 23CAP320 Design Thinking - Assignment II | **Programme:** II MCA, Semester III, Section A | **Institution:** Karpagam College of Engineering (Autonomous)
**Student:** Kavipriyadharsan P | **Roll No.:** 717825Z129 | **Academic year:** 2026-2027

---
## 1. Title
Smart Logistics Delivery Prediction System - Improving On-Time Delivery Predictability in Logistics.

## 2. Abstract
Late and unpredictable deliveries damage customer trust and increase cost for logistics companies. This project applies the Design Thinking process
(Empathize, Define, Ideate, Prototype, Test) to the problem and builds a working web prototype. The system predicts the delivery time of each shipment with a
RandomForest regression model using distance, traffic, weather, vehicle type, hour and day, warehouse delay and previous route delay. A transparent rule-based
layer compares the prediction with the promised time to classify delay risk as LOW, MEDIUM or HIGH, lists the reasons, and raises dashboard alerts for HIGH-risk shipments.
Managers can store prediction history, compare predicted and actual times, view analytics and run what-if simulations. The solution uses React, FastAPI,
PostgreSQL and scikit-learn, is packaged with Docker Compose and validated by automated tests and a GitHub Actions CI/CD pipeline. The model is trained on a synthetic
dataset, so the reported accuracy demonstrates the pipeline and is not a claim about real-world performance.

## 3. Introduction
Delivery promises are the visible part of logistics. When a promise is missed, the customer notices before the manager does. Predictive analytics can estimate
delays from conditions that are known at dispatch time, giving managers time to react. This report describes the design, implementation, testing and DevOps strategy
of a prototype that does this.

## 4. Problem Statement
Logistics managers cannot see which shipments are likely to miss the promised delivery time until it is too late to act. Static ETAs ignore traffic, weather,
warehouse queues and vehicle type, so customers receive unreliable estimates and complaints rise.

## 5. Objectives
1. Manage and track shipments. 2. Predict ETA. 3. Predict delay risk and classify it LOW/MEDIUM/HIGH. 4. Explain the factors behind the risk.
5. Show everything on a dashboard and alert on HIGH risk. 6. Store prediction history and compare with actual delivery. 7. Provide analytics and a what-if simulation.
8. Run locally with Docker, be tested automatically and have CI/CD and documentation.

## 6. Existing System
Spreadsheets, phone calls and basic tracking screens; ETAs are fixed estimates; delays are discovered reactively; no explanation of why a shipment is risky;
no feedback loop measuring how good the estimates were.

## 7. Proposed System
A web application where each shipment automatically receives an ML-based ETA, risk level, probability score and reasons; high-risk shipments create alerts;
history and analytics measure prediction quality; a what-if tool tests corrective options.

## 8. Design Thinking Process
Full detail in `docs/DESIGN_THINKING.md`.
- **Empathize:** observe operations managers, dispatchers and customers; main insight - delays are discovered too late.
- **Define:** persona and problem statement (below).
- **Ideate:** ML ETA prediction, risk dashboard with alerts, what-if simulator (selected); customer SMS tracking and auto re-routing (future).
- **Prototype:** wireframes, then the working application in this repository.
- **Test:** task-based usability tests with managers, SUS score, and prediction-accuracy metrics (user tests are planned; automated tests and accuracy metrics were executed).

## 9. User Persona
**Ravi Kumar, Logistics Operations Manager** - responsible for 120-200 daily shipments, measured on on-time % and complaints. Wants early warning, reasons and
options; frustrated by late information and manual follow-up.

## 10. How Might We Statement
*How might we predict delivery delays early enough for logistics managers to take corrective action and provide customers with more reliable delivery times?*

## 11. Ideation
(1) ML ETA prediction, (2) risk classification dashboard with alerts and reasons, (3) what-if simulation, (4) customer SMS/live tracking (future), (5) automatic re-routing (future).
Ideas 1-3 were selected using an impact/effort comparison and are implemented.

## 12. Prototype
The prototype concept tested first is the dashboard + shipment detail page showing ETA, risk badge and reasons. The final prototype is a full-stack application
with real prediction, database, alerts and analytics (screens: Login, Dashboard, Shipments, Shipment detail, Predictions, Alerts, Analytics, What-If, Settings).

## 13. System Architecture
React frontend -> REST API (FastAPI) -> PostgreSQL and the ML prediction service -> `eta_model.joblib` -> ETA + risk result. See `docs/ARCHITECTURE.md`.

## 14. Functional Requirements
FR1 Login (JWT). FR2 Create/read/update/delete shipments. FR3 Predict ETA for any input. FR4 Classify risk LOW/MEDIUM/HIGH with configurable thresholds.
FR5 Show risk reasons. FR6 Store every prediction. FR7 Create alerts for HIGH-risk active shipments; mark read. FR8 Dashboard KPIs and charts.
FR9 Analytics (summary, risk distribution, performance, accuracy). FR10 What-if simulation. FR11 Seed demo data.

## 15. Non-functional Requirements
Usability (clean responsive UI, understandable risk labels); Performance (single prediction well under one second; model loaded once);
Security (bcrypt, JWT, validation, CORS, no secrets in Git); Reliability (health endpoint, error handling, retries while the DB starts);
Portability (Docker Compose); Maintainability (layered code, config-driven thresholds, tests); Explainability (reasons for every risk).

## 16. Technology Stack
React 18 + Vite + Recharts + Axios; FastAPI + Pydantic + SQLAlchemy; PostgreSQL 16; pandas, NumPy, scikit-learn, joblib; Docker/Compose; GitHub Actions; pytest and Vitest.

## 17. Database Design
Tables `users`, `shipments`, `prediction_history`, `alerts` (columns in `docs/ARCHITECTURE.md`). One shipment has many predictions and many alerts;
deleting a shipment removes both. `prediction_history.shipment_id` is nullable so ad-hoc predictions can be stored.

## 18. ML Methodology
Dataset: 2,500 synthetic rows (`data/logistics_delivery_data.csv`) generated with realistic relationships and noise (documented in `ml/README.md`).
Pipeline: clean -> `ColumnTransformer` (one-hot for traffic/weather/vehicle, numeric passthrough) -> `RandomForestRegressor(100 trees, max_depth 12, min_samples_leaf 5)`.
80/20 train/test split (random_state 42). Metrics on 500 held-out rows:

| Metric | Value |
|---|---|
| MAE | 24.81 min |
| RMSE | 40.14 min |
| R2 | 0.9777 |

The very high R2 reflects the rule-generated synthetic data; real data would give lower scores. Preprocessing and model are saved together with joblib.

## 19. ETA Prediction
`predicted_delivery_minutes` = model output (rounded, at least 1). `predicted_eta` = dispatch time + predicted minutes. Example from the running system:
50 km, HIGH traffic, RAIN, TRUCK, 15:00 Wednesday, 10 min warehouse delay, 5 min previous delay, promised 90 min -> predicted 144 min, HIGH risk.

## 20. Delay Risk Prediction
`ratio = predicted / promised`. LOW if ratio <= 1.00; MEDIUM if <= 1.15; HIGH above 1.15 (set in configuration).
`delay_probability = 1 / (1 + exp(-(predicted - promised)/scale))` with `scale = max(10, 0.08 x promised)`; a simple, documented score between 0 and 1.
**It is not a statistically calibrated probability.** Reasons come from rules on the inputs (high traffic, rain/storm, distance >= 300 km, warehouse delay >= 20 min,
previous delay >= 15 min, peak hour, and "historical route delay" when at least 3 completed shipments on the same route and >= 50% were late).

## 21. Scrum Development Plan
Roles, backlog and sprint plan are in `docs/SCRUM_PLAN.md`. Product Owner = logistics stakeholder; Scrum Master facilitates; Development Team = full-stack, ML, UI/UX, DevOps.

## 22. Product Backlog
US1 dashboard (8), US2 ETA prediction (13), US3 risk with reasons (8), US4 alerts (5), US5 shipment management (5), US6 what-if (5), US7 accuracy analytics (5),
US8 secure login (3), US9 CI/CD and Docker (5) - 57 points in total.

## 23. Sprint Plan
Sprint 1 (2 weeks, 34 points): goal "log in, create shipments, get ML ETA + risk + reasons on a dashboard" (US8, US5, US2, US3, US1-basic). Metrics: velocity,
burndown and test pass rate (illustrative values in the plan). Sprint 2: alerts, what-if, accuracy analytics, CI/CD.

## 24. XP Practice
Test-First Development: failing tests for risk rules, ML behaviour and API contracts were written before the implementation; CI runs them on every push.
See `backend/tests/` and `docs/SCRUM_PLAN.md`.

## 25. Business Outcomes
**Targeted outcome: customer trust through improved delivery predictability** (supported by fewer complaints, lower cost and better operational efficiency).

| Outcome | How the solution contributes | Indicator to track |
|---|---|---|
| Customer trust | Promises based on predicted time and early warning when a promise is at risk | on-time %, complaints per 1,000 deliveries |
| Improved predictability | ETA error is measured continuously (MAE, within-15-minutes %) | MAE trend |
| Reduced complaints | Customers are warned before the promised time passes | complaint count, "where is my order" calls |
| Cost reduction | Fewer penalty/redelivery/support costs; better vehicle choice via what-if | cost per delivery |
| Operational efficiency | Managers focus on the HIGH-risk list instead of checking everything | shipments handled per manager |

**Traditional management thinking vs innovation-driven, design-led strategy**

| | Traditional | Design-led (this project) |
|---|---|---|
| Starting point | Internal targets and reports | The manager's and customer's real pain |
| Timing | Reacts after the delay | Predicts before the delay |
| Planning | Fixed ETA, big-bang system | Prototype, test with users, iterate |
| Decisions | Experience and intuition | Data + explainable reasons + what-if |
| Success measure | Output (shipments moved) | Outcome (reliability, trust) |
| Risk handling | Avoid change | Learn quickly through small experiments |

**Risk / trade-off:** prediction accuracy can be affected by unexpected events (sudden traffic jams, road closures, severe weather, breakdowns) that are not in the input
data. Managers may over-trust the output. Mitigation: show reasons and a "heuristic score" label, keep a human in the loop, monitor the error continuously and retrain,
add live data feeds in the future. A second trade-off: too many alerts cause alert fatigue, so thresholds are configurable.

## 26. CI/CD Pipeline
Commit -> Build -> Test -> Docker build/smoke test -> Deploy-ready (publish images on tags). Version control with Git branches/PRs; build automation with pip/npm/Docker;
configuration management with environment variables and `.env.example`. CI validates every push within minutes. Details in `docs/CICD.md`.

## 27. DevOps Strategy
Containerize (backend, frontend, PostgreSQL), continuously deploy tagged images, test continuously and monitor continuously (health checks, logs, model-error metrics).
DevOps extends Agile by automating delivery and operations. Details in `docs/DEVOPS.md`.

## 28. Containerization
Two Dockerfiles (backend non-root with health check; frontend multi-argument build) and `docker-compose.yml` with PostgreSQL volume and health-based start order.
Run: `docker compose up --build`.

## 29. Continuous Testing
Unit (risk rules, ML wrapper), API integration, frontend component tests, container smoke test; all automatic in CI.

## 30. Continuous Monitoring
`/health` endpoint, application logs, Analytics page for model error and drift; future Prometheus/Grafana.

## 31. Testing
| Suite | Tests | Covers |
|---|---|---|
| `backend/tests/test_api.py` | 25 | health, auth (success/failure/401), shipment CRUD, validation 400, 404, duplicate IDs, prediction, history storage, what-if, alerts, analytics, settings |
| `backend/tests/test_risk.py` | 6 | thresholds, probability bounds/monotonicity, reasons |
| `backend/tests/test_ml.py` | 5 | model file, numeric/non-negative output, required features, learned relationships |
| `frontend/src/*.test.*` | 12 | formatters, error messages, UI components, protected route |
Total 48 automated tests. Backend tests and the end-to-end flows were also executed against a real PostgreSQL 16 instance during development, and the UI was exercised in a headless browser.

## 32. Results
- Model on held-out synthetic test data: MAE 24.81 min, RMSE 40.14 min, R2 0.9777.
- On the seeded demo shipments (generated with a different random seed, so unseen by the model) the running system reported an average ETA error of about 30 minutes
  and about 82% correct on-time/late calls (values shown on the dashboard; they change as data changes).
- All required screens and API endpoints work end to end with a PostgreSQL database.
These numbers describe a synthetic setting and must not be presented as real-world accuracy.

## 33. Limitations
Synthetic data; no live traffic/weather/GPS; heuristic (uncalibrated) probability; one user role; JWT in localStorage; no SMS/e-mail; the CD workflow publishes images but
final server deployment is manual; user-testing results in the Design Thinking section are a plan, not collected data.

## 34. Future Enhancements
Real data and retraining pipeline, live traffic/weather APIs, probability calibration, route-level models, role-based access, e-mail/WhatsApp alerts, customer tracking page,
Kubernetes deployment, Prometheus/Grafana monitoring, A/B testing of promised times.

## 35. Conclusion
The project shows how Design Thinking leads from a user problem to a concrete solution: an explainable, data-driven early-warning system for late deliveries.
It is implemented as a working, containerised, tested application with an automated pipeline. With real data and live feeds it could improve customer trust, reduce complaints and cost,
and make logistics operations more efficient.

## References
FastAPI, SQLAlchemy, scikit-learn, React, Recharts and Docker official documentation; Scrum Guide (Schwaber and Sutherland); Beck, *Extreme Programming Explained*;
IDEO / Stanford d.school Design Thinking resources; Humble and Farley, *Continuous Delivery*.
