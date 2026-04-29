# ── Saheli Backend — Dockerfile ──────────────────────────────────────────────
# Builds the FastAPI triage server.
# Model weights (~2.5 GB GGUF) are NOT baked in — mount via docker-compose volume.
#
# CPU build (default):
#   docker compose up --build
#
# GPU build (CUDA 12.2):
#   docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build

FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ffmpeg \
    espeak-ng \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python build tools first (some packages need them)
COPY requirements.txt .
RUN pip install --no-cache-dir setuptools wheel

# llama-cpp-python — CPU build.
# For GPU inference, override at build time:
#   --build-arg LLAMA_CPP_INDEX=https://abetlen.github.io/llama-cpp-python/whl/cu122
ARG LLAMA_CPP_INDEX=https://abetlen.github.io/llama-cpp-python/whl/cpu
RUN pip install --no-cache-dir llama-cpp-python \
    --extra-index-url ${LLAMA_CPP_INDEX}

# Remaining runtime deps (excludes unsloth/trl — training only, Kaggle/Colab)
RUN pip install --no-cache-dir \
    openai-whisper \
    transformers \
    torch \
    imageio-ffmpeg \
    fastapi \
    "uvicorn[standard]" \
    python-multipart \
    pyaudio \
    pyttsx3 \
    opencv-python-headless \
    Pillow \
    datasets \
    geopy \
    scikit-learn \
    huggingface_hub \
    pytest

# Copy application source (model *.gguf files excluded via .dockerignore)
COPY config/   config/
COPY core/     core/
COPY data/     data/
COPY audio/    audio/
COPY vision/   vision/
COPY ui/       ui/
COPY models/   models/
COPY tests/    tests/
COPY run.py    .

# Runtime directories
RUN mkdir -p data/uploads logs

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

CMD ["python", "run.py"]
