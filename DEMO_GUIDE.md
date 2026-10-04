# Demo Guide (5-10 minutes)

Before you start: `docker compose up --build`, wait ~1-2 minutes, open http://localhost:5173. Optional: open http://localhost:8000/docs in another tab.
(Numbers on screen come from the live model and database, so yours may differ slightly from the examples below.)

## Demo flow
| Min | Step | What to say / do |
|---|---|---|
| 0:00 | **1. Login** | `admin@logistics.local` / `Admin@123`. "JWT authentication; password is stored hashed with bcrypt." (Optionally show a wrong password -> error.) |
| 0:30 | **2. Dashboard** | "All 8 cards and 5 charts are computed from PostgreSQL, nothing is hard-coded." Point at total / active / high-risk / average ETA error / on-time prediction %. |
| 1:30 | **3. Charts** | Status distribution, risk distribution, predicted vs actual line chart, error by day, performance over time. |
| 2:30 | **4. Shipments** | Search, filter by HIGH risk. Click **+ New shipment**: Chennai -> Madurai, 460 km, HIGH traffic, STORM, TRUCK, promised 800 min -> Create. "The model predicts immediately and an alert is raised." |
| 3:30 | **5. Shipment detail (L001)** | Show details, promised vs predicted bars, risk badge, delay probability, **risk reasons** (high traffic, rain, long distance...). Click **Run prediction** -> new row in prediction history. |
| 4:30 | **6. Predictions page** | Use the default input (50 km, HIGH, RAIN, TRUCK, promised 90) -> predicted ~144 min, HIGH. "This is a real RandomForest prediction; the risk comes from predicted vs promised." |
| 5:30 | **7. Alerts** | Show alert text "Shipment ... predicted to be delayed by approximately N minutes", reason, ETA. Mark one as read; badge in the sidebar drops. |
| 6:00 | **8. Analytics** | MAE, RMSE, within 15 min %, on-time call accuracy, predicted-vs-actual scatter. "Prediction error = ABS(actual - predicted) stored in prediction_history." |
| 7:00 | **9. What-if** | Pick a HIGH-risk shipment, set Traffic HIGH -> LOW (or switch vehicle), **Run simulation**. "The model is called again with the changed inputs - the difference is not a fixed number." Show original vs new, difference, risk change. |
| 8:00 | **10. Docker** | Show `docker-compose.yml`: postgres + backend + frontend, health checks, one command. |
| 8:45 | **11. CI/CD** | Show `.github/workflows/ci.yml`: commit -> build -> test -> docker build -> ready. Mention 48 automated tests. |
| 9:30 | **12. Close** | Limitations: synthetic data, heuristic probability, no live feeds. Future work. |

Backup if something fails: http://localhost:8000/docs lets you call every endpoint (click **Authorize**, username = email).

## Possible viva questions
1. **What problem does your project solve?** Managers learn about delays too late; the system predicts delivery time and delay risk early and explains why.
2. **Why Random Forest?** Handles non-linear relationships and mixed features, needs little tuning, is robust to noise and gives feature importances.
3. **What are the features and target?** Features: distance, traffic, weather, vehicle, hour, day, warehouse delay, previous route delay. Target: actual delivery minutes.
4. **How is risk decided?** Ratio predicted/promised: <=1.00 LOW, <=1.15 MEDIUM, above HIGH; thresholds are in configuration.
5. **Is delay_probability a real probability?** No. It is a documented heuristic score from the gap between predicted and promised time; it is not calibrated.
6. **Where does the data come from?** A synthetic dataset generated with realistic rules and noise; documented as such. Real data would be needed for real accuracy.
7. **Why is R2 so high?** Because the synthetic data follows simple rules; real data would give a lower score.
8. **How do you explain a prediction?** Rule-based reasons from the inputs (traffic, weather, distance, delays, peak hour, route history).
9. **How does the what-if work?** The backend re-runs the model with overridden inputs and compares both predictions; nothing is saved.
10. **How is data stored?** PostgreSQL via SQLAlchemy: users, shipments, prediction_history, alerts.
11. **How is security handled?** bcrypt hashing, JWT with expiry, env-based secrets, CORS allow-list, Pydantic validation, ORM; demo credentials are local only.
12. **What is in the CI pipeline?** Train model, pytest, Vitest, frontend build, Docker build and smoke test; images published on tags.
13. **Why Docker?** Same environment everywhere, one command to run the whole stack.
14. **Scrum vs DevOps?** Scrum organises the work in sprints; DevOps automates build/test/deploy/monitor. They complement each other.
15. **Which XP practice did you use?** Test-first development (and continuous integration): tests for risk rules and ML behaviour were written first.
16. **Biggest risk?** Unexpected events (traffic jams, closures, storms) are not in the data, so predictions can be wrong; mitigate with monitoring, human review and live feeds.
17. **How would you improve it?** Real data, live traffic/weather APIs, calibration, retraining pipeline, role-based access, SMS/e-mail alerts, monitoring dashboards.
18. **How do you measure accuracy?** MAE, RMSE, within-15-minute %, and on-time/late call accuracy on the Analytics page.
