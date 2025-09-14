# Root-level Dockerfile (next to your README)
FROM python:3.11-slim

WORKDIR /app

# System deps for building scientific wheels (numpy/pandas/lightgbm)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps from the project subfolder
COPY signal/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code from the subfolder
COPY signal/ .

# Run both the bot and workers via supervisord
CMD ["supervisord", "-c", "/app/supervisord.conf"]
