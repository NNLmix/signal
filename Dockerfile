FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Koyeb health check требует web-сервер → uvicorn слушает 8000
CMD ["python", "-u", "main.py"]
