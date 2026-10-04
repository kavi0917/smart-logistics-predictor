# CI/CD Pipeline (Question 4)

```
COMMIT  ->  BUILD  ->  TEST  ->  DOCKER BUILD  ->  DEPLOY / READY FOR DEPLOYMENT
 (git)    (pip, npm)  (pytest,    (images +          (publish images,
                       vitest)     smoke test)        run on a server)
```

## 1. Version control (Git + GitHub)
- Repository `smart-logistics-predictor`; branches: `main` (always releasable), `feature/*` per user story, pull requests with review and CI checks required before merge.
- Conventional commit messages (`feat:`, `fix:`, `test:`, `docs:`); version tags `v1.0.0` trigger the CD workflow.
- `.gitignore` keeps `.env`, virtual environments, `node_modules`, caches and databases out of Git.

## 2. Build automation
- Backend: `pip install -r backend/requirements-dev.txt`, compile check, **dataset generation and model training** (`ml/generate_dataset.py`, `ml/train_model.py`).
- Frontend: `npm ci` and `npm run build` (Vite) produce the production bundle.
- Docker: `docker compose build` builds the backend and frontend images.

## 3. Configuration management
- All environment-specific values come from environment variables (`.env.example` documents them): `DATABASE_URL`, `SECRET_KEY`, `JWT_EXPIRE_MINUTES`,
  `MODEL_PATH`, `CORS_ORIGINS`, `VITE_API_URL`, risk thresholds.
- `.env` is never committed; CI creates it from `.env.example`; real secrets belong in GitHub **Secrets/Variables**.
- Infrastructure is declared in `docker-compose.yml` (same stack on every machine).

## 4. Pipeline stages (`.github/workflows/ci.yml`)
| Stage | Job | What runs |
|---|---|---|
| Commit | trigger | `on: push` and `on: pull_request` |
| Build + Test (backend) | `backend` | install, train/evaluate model, compile check, **pytest (36 tests)** |
| Build + Test (frontend) | `frontend` | `npm ci`, **Vitest (12 tests)**, `npm run build` |
| Docker | `docker` | validate compose, build images, start stack, wait for `/health`, smoke-test login + prediction, tear down |
| Deploy-ready | `ready` | runs only if everything above passed |
`.github/workflows/cd.yml` (on version tags or manual run) builds and pushes both images to GitHub Container Registry. On a server:
`docker compose pull && docker compose up -d`. No paid cloud service is required.

## 5. How Continuous Integration validates changes frequently
Every push/PR automatically builds and tests the whole system in a clean environment, so integration problems (a broken import, a changed API, a model
that no longer trains, a failing build) are found within minutes of the commit instead of at the end of the project. Small frequent merges keep
`main` green; failing checks block the merge; the same pipeline is the safety net for TDD.
