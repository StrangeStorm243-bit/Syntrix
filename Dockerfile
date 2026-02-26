FROM python:3.11-slim

WORKDIR /app

# Install system deps (gcc for C extensions, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir ".[bridge]"

# Copy project files
COPY projects/ projects/

# Create data directory
RUN mkdir -p /app/data

ENV SIGNALOPS_DB_URL=sqlite:///data/signalops.db
ENV SIGNALOPS_API_HOST=0.0.0.0
ENV SIGNALOPS_API_PORT=8400

EXPOSE 8400

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD curl -f http://localhost:8400/api/health || exit 1

CMD ["uvicorn", "signalops.api.app:create_app", "--host", "0.0.0.0", "--port", "8400", "--factory"]
