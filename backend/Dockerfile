FROM python:3.11-slim

# Install system dependencies required for GDAL / rasterio
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all flat modules into container root
COPY . .

# Set Python path so root modules are discoverable
ENV PYTHONPATH=/app

EXPOSE 8000

# Updated entrypoint pointing directly to ingest_api/main.py
CMD ["uvicorn", "ingest_api.main:app", "--host", "0.0.0.0", "--port", "8000"]