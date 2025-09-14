# Dockerfile (repo root)

FROM python:3.11-slim

# Make Python friendlier in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (only what pip builds might need)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# ---- Install Python deps
# requirements.txt is at repo root
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy app code (repo root -> /app)
COPY . .

# If supervisord.conf uses relative paths, it's now at /app/supervisord.conf
CMD ["supervisord", "-c", "/app/supervisord.conf"]
