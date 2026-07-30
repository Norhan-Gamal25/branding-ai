# Branding AI — Backend Dockerfile
# Python 3.11-slim + DejaVu fonts for Unicode PDF generation

FROM python:3.11-slim

WORKDIR /app

# ── System dependencies ────────────────────────────────────────────────────────
# gcc/g++/libffi-dev : required by some CrewAI/LiteLLM native extensions
# fonts-dejavu-core  : DejaVu TTF fonts — enables Arabic, Hebrew, CJK in PDF output
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc g++ libffi-dev \
      fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ────────────────────────────────────────────────────────
# uv is used instead of pip: its resolver handles deep transitive graphs
# (crewai + litellm + google-generativeai) without hitting pip's depth limit.
COPY requirements.txt .
RUN pip install --no-cache-dir uv \
 && uv pip install --system --no-cache -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY . .

# ── Runtime setup ─────────────────────────────────────────────────────────────
# Create export directory — mounted as a named volume in docker-compose
RUN mkdir -p /tmp/exports

EXPOSE 8000

# Use 1 worker (CrewAI pipeline is CPU/IO bound, not embarrassingly parallel)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
