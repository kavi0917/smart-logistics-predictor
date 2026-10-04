# Build context is the PROJECT ROOT (see docker-compose.yml) so the image can include ml/, data/ and models/.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY backend/ backend/
COPY ml/ ml/
COPY data/ data/
COPY models/ models/
COPY scripts/ scripts/

# The trained model is committed to the repo; if it is missing, train it during the image build.
RUN [ -f models/eta_model.joblib ] || python ml/train_model.py

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status == 200 else 1)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
