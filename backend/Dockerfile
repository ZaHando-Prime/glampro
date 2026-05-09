# ============================================================
# Glam Pro Beauty Assistant – Dockerfile
# ============================================================
# Multi-stage build using Python 3.11 slim.
# The GGUF model is NOT baked into the image; mount it as a volume.
# ============================================================

FROM python:3.11-slim AS base

# Install system-level build tools required by llama-cpp-python and chromadb
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        libopenblas-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- dependency layer (cached separately from source code) ----
COPY requirements.txt .
# CPU-only build by default. For CUDA, set CMAKE_ARGS="-DLLAMA_CUDA=on" as a build arg.
ARG CMAKE_ARGS=""
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- source code ----
COPY . .

# Create directories that the app needs at runtime
RUN mkdir -p ./models ./chroma_data ./data

# ---- runtime config ----
# Override via docker run -e MODEL_PATH=... or docker-compose environment block
ENV MODEL_PATH=./models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
    ADMIN_API_KEY=change-me-in-production \
    CHROMA_PATH=./chroma_data \
    DATA_DIR=./data \
    LLM_N_CTX=4096 \
    LLM_N_THREADS=8 \
    LLM_MAX_TOKENS=512 \
    LLM_TEMPERATURE=0.7 \
    LLM_TOP_P=0.95

EXPOSE 8000

# Mount point for the GGUF model (keep it outside the image for size)
VOLUME ["/app/models", "/app/chroma_data"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
