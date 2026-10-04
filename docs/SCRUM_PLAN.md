# Scrum-based Development Plan (Question 1)

## 1. Scrum team roles
| Role | Responsibility in this project |
|---|---|
| **Product Owner** | Owns the product backlog and priorities; represents logistics managers (e.g. a logistics operations head / faculty guide acting as stakeholder). Accepts or rejects work at the sprint review. |
| **Scrum Master** | Facilitates daily scrum, planning, review, retrospective; removes blockers; protects the team from scope creep. |
| **Development Team** (self-organising, 3-5 people) | Full-stack developer, ML engineer, UI/UX designer, DevOps/QA engineer. Delivers a potentially shippable increment each sprint. |
Because this is an individual college project, one student plays several roles; the plan shows how a real team would organise.

## 2. Product backlog (priority order)
| ID | User story | Priority | Story points |
|---|---|---|---|
| US1 | As a **logistics manager**, I want to see a dashboard of shipment status and delay risk so that I can spot problems at a glance. | Must | 8 |
| US2 | As a **manager**, I want the system to predict a shipment's delivery time (ETA) from traffic, weather, distance and vehicle so that I can promise realistic times. | Must | 13 |
| US3 | As a **manager**, I want each shipment classified LOW / MEDIUM / HIGH risk **with reasons** so that I understand why it may be late. | Must | 8 |
| US4 | As a **manager**, I want an alert when a shipment becomes HIGH risk so that I can act before the delay happens. | Must | 5 |
| US5 | As a **dispatcher**, I want to create and edit shipments so that the data stays current. | Must | 5 |
| US6 | As a **manager**, I want a what-if simulation so that I can see how changing vehicle/traffic/delays changes the ETA. | Should | 5 |
| US7 | As an **analyst**, I want predicted vs actual delivery time and accuracy metrics so that I can trust the model. | Should | 5 |
| US8 | As an **admin**, I want secure login so that only authorised staff see shipment data. | Must | 3 |
| US9 | As a **developer**, I want automated build/test/deploy (CI/CD, Docker) so that every change is validated. | Should | 5 |
Total: 57 points.

## 3. Sprint plan - Sprint 1 (2 weeks)
**Sprint goal:** *"A manager can log in, create shipments, get an ML-based ETA with a LOW/MEDIUM/HIGH risk and reasons, and see it on a dashboard."*

**Sprint backlog** (selected from the product backlog; 34 points):
| Story | Tasks | Points |
|---|---|---|
| US8 Login | JWT auth endpoint, password hashing, login page | 3 |
| US5 Shipment CRUD | DB models, REST endpoints, shipment table + form | 5 |
| US2 ETA prediction | generate dataset, train RandomForest, save pipeline, `/predict` endpoint | 13 |
| US3 Risk + reasons | risk thresholds in config, classifier, reason rules, badges in UI | 8 |
| US1 Dashboard (basic) | summary endpoint, KPI cards, risk chart | 5 |
Remaining stories (US4 alerts, US6 what-if, US7 accuracy, US9 CI/CD) go to Sprint 2 (23 points).

**Definition of Done:** code reviewed, unit/API tests passing in CI, runs in Docker, documented, demoed to the Product Owner.

## 4. Tracking metrics
1. **Velocity** - story points completed per sprint. Planned Sprint 1 = 34. Illustrative result: 31 completed (US1 partly carried over) -> use ~31-34 to plan Sprint 2.
2. **Burndown** (ideal vs actual remaining points over the 10 working days):

| Day | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ideal | 34 | 31 | 27 | 24 | 20 | 17 | 14 | 10 | 7 | 3 | 0 |
| Actual (illustrative) | 34 | 34 | 30 | 28 | 24 | 21 | 18 | 13 | 9 | 6 | 3 |
Actual above ideal early on shows the learning cost of the ML pipeline; the team caught up after day 6.
3. **Test pass rate / defect count** - % of automated tests passing in CI and bugs found per sprint (target: 100% passing before merge).
(The velocity and burndown figures are *illustrative sample data for the assignment*, not measured values.)

## 5. XP practice: Test-First Development (TDD)
Cycle: **Red** (write a failing test) -> **Green** (write the minimum code to pass) -> **Refactor**.
How it supports this solution:
- Risk rules are pure functions - tests such as `classify_risk(130, 100) == "HIGH"` and "probability is monotonic and between 0 and 1" were written **before**
  the thresholds were coded, so the business rules are unambiguous (see `backend/tests/test_risk.py`).
- ML tests guard the pipeline: model file exists, prediction is numeric and never negative, more traffic/storm/distance/warehouse delay increases the
  ETA (`backend/tests/test_ml.py`). A bad retraining run fails CI instead of reaching users.
- API tests (`test_api.py`) describe expected behaviour (401 without token, 404 for missing shipment, 400 for invalid data) and make refactoring safe.
- Benefits: fewer regressions, living documentation, confidence to change thresholds or retrain the model.
Related XP practice used alongside: **Continuous Integration** (GitHub Actions runs all tests on every push).

## 6. Scrum events
Sprint planning (2 h), daily scrum (15 min), sprint review (demo of the working increment), sprint retrospective (what to improve), backlog refinement.
