# --- BACKEND STAGE ---
FROM python:3.11-slim as backend

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- FRONTEND (For production build) ---
# For the hackathon/demo, we can run them separately or 
# use a multi-stage build to serve React via FastAPI.
