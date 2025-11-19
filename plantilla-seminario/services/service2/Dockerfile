FROM python:3.12-slim
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ejecuta la aplicación FastAPI en el puerto 8004
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]

