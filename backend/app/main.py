import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.ml.predictor import ModelNotAvailable, predictor
from app.routers import alerts, analytics, auth, predictions, settings as settings_router, shipments
from app.services.seed_service import ensure_demo_user, seed_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("logistics")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        if settings.seed_on_startup:
            seed_all(db)
        else:
            ensure_demo_user(db)
    finally:
        db.close()
    try:
        predictor.load()
    except ModelNotAvailable as exc:
        logger.error("%s", exc)
    yield


app = FastAPI(
    title="Smart Logistics Delivery Prediction API",
    description="Academic prototype: ETA prediction and delay-risk classification for logistics shipments.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]} for e in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": "Invalid data", "errors": errors})


@app.exception_handler(StarletteHTTPException)
async def http_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=getattr(exc, "headers", None))


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)  # stack trace goes to the log only
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", tags=["Health"])
def health():
    from sqlalchemy import text

    db_ok = True
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    finally:
        db.close()
    model_ok = predictor.path.exists()
    return {"status": "ok" if db_ok and model_ok else "degraded", "database": db_ok, "model_file": model_ok}


app.include_router(auth.router)
app.include_router(analytics.dashboard_router)
app.include_router(shipments.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(analytics.analytics_router)
app.include_router(settings_router.router)
