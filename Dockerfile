# Dockerfile (repo root)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install deps first for better caching
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# --- NEW: copy the model directory explicitly (robust vs .dockerignore) ---
COPY models/ /app/models/

# Run everything under supervisord (you already have this file)
CMD ["supervisord", "-c", "/app/supervisord.conf"]
