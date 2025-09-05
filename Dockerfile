# Use official Python image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# Workdir
WORKDIR /app

# System deps for building wheels (cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN python - <<'PY'
import sys
from pathlib import Path

p = Path('requirements.txt')
data = p.read_bytes()
# Normalize: remove NULs and CR, unify newlines to LF
normalized = data.replace(b'\x00', b'').replace(b'\r\n', b'\n').replace(b'\r', b'\n')
if normalized != data:
    p.write_bytes(normalized)
    print(f"Normalized requirements.txt. Size: {len(normalized)} bytes", file=sys.stderr)
else:
    print("requirements.txt already normalized", file=sys.stderr)
PY
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Expose port (Railway will set PORT env)
EXPOSE 8080

# Run uvicorn with sh -c to properly handle environment variables
CMD ["sh", "-c", "uvicorn web.main:app --host 0.0.0.0 --port ${PORT}"]
