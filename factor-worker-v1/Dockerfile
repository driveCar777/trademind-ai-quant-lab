FROM python:3.10-alpine

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apk add --no-cache curl

WORKDIR /app

COPY server.py /app/server.py

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["python3", "/app/server.py"]
