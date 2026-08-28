# TradeMind Monitor Agent - ARM64 for AGX Xavier
FROM nvcr.io/nvidia/l4t-pytorch:r32.1-py3

LABEL maintainer="TradeMind AI"
LABEL version="1.0.0"
LABEL description="Monitor Agent for AGX Xavier - System Monitoring and Health Checks"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip setuptools wheel

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
COPY src/ /app/src/

ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

CMD ["python3", "-m", "src.main"]
