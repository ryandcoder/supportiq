FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# /app/data  : your CSV files (mounted read-only by docker-compose)
# /app/runtime: data quality report (named volume, writable)
RUN useradd --create-home appuser && mkdir -p /app/data /app/runtime && chown -R appuser /app/runtime
USER appuser

EXPOSE 8000
# 1) make sure the database holds the data  2) start the API
CMD ["sh", "-c", "python -m app.data_pipeline.bootstrap && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
