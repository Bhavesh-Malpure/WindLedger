
FROM python:3.12-slim

# Keep Python output visible and avoid unnecessary bytecode files.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# The backend working directory inside the container.
WORKDIR /app

# Install dependencies separately to improve build caching.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code and fixture datasets.
COPY app/ ./app/
COPY fixtures/ ./fixtures/

# FastAPI listens on port 8000 inside the container.
EXPOSE 8000

# Start the API without development auto-reload.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
