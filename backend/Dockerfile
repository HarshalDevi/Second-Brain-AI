FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PYTHONUNBUFFERED=1

# IMPORTANT: shell form so $PORT expands
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"