FROM python:3.11-slim

WORKDIR /code

# Build context is project root (set via docker-compose context: .)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/
COPY mock_data.json ./mock_data.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
