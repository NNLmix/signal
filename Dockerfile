FROM python:3.11-slim

WORKDIR /app

# Install system deps for numpy/pandas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from signal folder
COPY signal/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY signal/ .

# Run main.py
CMD ["python", "main.py"]
