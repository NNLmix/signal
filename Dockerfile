FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port 8000 for Koyeb health check
EXPOSE 8000

CMD ["python", "-u", "main.py"]
