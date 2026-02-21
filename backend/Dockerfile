FROM python:3.12-slim

WORKDIR /app

# libgomp1 is the Linux OpenMP runtime required by XGBoost
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies via pip (simpler than uv inside Docker)
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        fastapi \
        "uvicorn[standard]" \
        python-multipart \
        httpx \
        "sqlalchemy[asyncio]" \
        asyncpg \
        alembic \
        "redis[hiredis]" \
        "celery[redis]" \
        pydantic-settings \
        xgboost \
        shap \
        pandas \
        numpy \
        scikit-learn \
        tqdm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy application code
COPY backend/ .

# Copy ML artifacts and demo data
COPY ml/artifacts/ /app/artifacts/
COPY ml/demo/ /ml/demo/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
