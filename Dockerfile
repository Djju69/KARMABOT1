FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

WORKDIR /app

# System deps (минимально достаточно)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    python3-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./ 
RUN python -m pip install --upgrade pip \
 && python -m pip install --no-cache-dir -r requirements.txt

# App
COPY . .

# Port (Railway передаёт PORT)
ENV PORT=8080
EXPOSE 8080

# Один корректный CMD
CMD ["uvicorn","web.main:app","--host","0.0.0.0","--port","${PORT}"]
