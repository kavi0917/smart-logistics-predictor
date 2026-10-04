# DevOps Deployment Strategy (Question 5)

## 1. Containerization
- **backend image** (`python:3.12-slim`): FastAPI app + ML model; runs as a non-root user; has a `HEALTHCHECK` on `/health`.
- **frontend image** (`node:22-alpine`): builds the React app and serves it.
- **postgres** (`postgres:16-alpine`) with a named volume for data and a health check.
- `docker-compose.yml` wires them: backend waits for a healthy database, frontend waits for a healthy backend. Same containers run on a laptop, CI and a server -
  "works on my machine" problems disappear.

## 2. Continuous Deployment
1. Merge to `main` -> CI passes -> tag `v1.x.x`.
2. `cd.yml` builds images and pushes them to the container registry (tagged with the version and commit SHA).
3. Target server: `docker compose pull && docker compose up -d` (rolling replace; keep the previous image tag for **rollback**).
4. Configuration (secrets, URLs) is injected via environment variables, not baked into images (except the browser-facing `VITE_API_URL` build argument).
The repository automates build + publish; the final server step is described but not automated because it needs infrastructure the student does not own.

## 3. Continuous Testing
| Level | Tool | When |
|---|---|---|
| Unit (risk rules, ML wrapper) | pytest | every push |
| API integration (real DB + model) | pytest + FastAPI TestClient | every push |
| Frontend components/utilities | Vitest + Testing Library | every push |
| Build / container smoke test | CI `docker` job | every push |
| Model quality | `evaluate_model.py` metrics, Analytics page (MAE, on-time accuracy) | each retrain / continuously on live data |
After each release a post-deploy smoke test (login + `/predict`) confirms the release works.

## 4. Continuous Monitoring
- **Health:** `/health` (database + model file) used by Docker health checks and uptime monitors.
- **Logs:** structured application logs (requests, alerts created, failed logins, unhandled errors with stack trace server-side only).
- **Business/ML monitoring:** the Analytics page tracks prediction error (MAE/RMSE), on-time prediction accuracy and risk distribution over time;
  a rising error is a signal of **model drift** and triggers retraining.
- **Future:** Prometheus metrics + Grafana dashboards and alerting on error rate and latency.

## 5. DevOps vs Agile-only workflow
| Aspect | Agile-only | DevOps (this project) |
|---|---|---|
| Focus | Iterative development with the customer | Development **and** delivery/operations as one flow |
| Release | Increment at sprint end, often manual hand-off to ops | Automated pipeline, release any time |
| Testing | Often manual QA near sprint end | Continuous automated tests on every commit |
| Environments | Differ between dev, test, prod | Identical containers everywhere |
| Feedback after release | Next sprint review | Continuous monitoring and alerts |
| Ownership | Developers "throw over the wall" to ops | Shared responsibility ("you build it, you run it") |
Agile makes *what* we build adaptable; DevOps makes *shipping and running* it fast and reliable. They complement each other.
