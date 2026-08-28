# TradeMind Backtest Worker - ARM64 for AGX Xavier
# Base: Python 3.8 with NVIDIA CUDA support for Jetson

FROM nvcr.io/nvidia/l4t-pytorch:r32.1-py3

LABEL maintainer="TradeMind AI"
LABEL version="1.0.0"
LABEL description="Backtest Worker for AGX Xavier - Strategy Backtesting Engine"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    libomp-dev \
    python3-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create app directory
WORKDIR /app

# Copy source code
COPY src/ /app/src/
COPY config/ /app/config/ 2>/dev/null || true

# Create results directory
RUN mkdir -p /app/results

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run the worker
CMD ["python3", "-m", "src.main"]
