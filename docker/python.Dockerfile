# =============================================================================
# Multi-target Python Dockerfile
# Targets: api, streamlit, calculator
# =============================================================================
# Build args — override BASE_IMAGE and TORCH_INDEX for GPU builds
ARG BASE_IMAGE=python:3.12-slim
ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu

# ---------------------------------------------------------------------------
# Stage: base — shared dependencies for all Python services
# ---------------------------------------------------------------------------
FROM ${BASE_IMAGE} AS base

# Re-declare after FROM so it's available in this stage
ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu

ARG API_PORT=8070
ARG STREAMLIT_PORT=8511
ARG CALCULATOR_PORT=8000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API_PORT=${API_PORT} \
    STREAMLIT_PORT=${STREAMLIT_PORT} \
    CALCULATOR_PORT=${CALCULATOR_PORT}

# System dependencies required by native packages (tantivy, lancedb, Pillow, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        sqlite3 \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (layer-cached separately from source)
COPY backend/requirements.txt /app/backend/requirements.txt
COPY pyproject.toml /app/pyproject.toml

# Install torch separately with the correct index, then the rest.
# When TORCH_INDEX=skip (GPU image already has PyTorch), skip the torch install.
RUN if [ "${TORCH_INDEX}" != "skip" ]; then \
        pip install --no-cache-dir \
            torch torchvision torchaudio \
            --index-url "${TORCH_INDEX}"; \
    fi \
    && pip install --no-cache-dir \
        -r backend/requirements.txt

# Copy full source tree
COPY backend/ /app/backend/
COPY advisor_pipeline/ /app/advisor_pipeline/

# Editable install of the project (registers advisor_pipeline package).
# Must run after source is copied so setuptools can discover packages.
RUN pip install --no-cache-dir -e .

# Ensure data directory exists
RUN mkdir -p /app/backend/data

# ---------------------------------------------------------------------------
# Target: api — FastAPI backend (configurable via API_PORT)
# ---------------------------------------------------------------------------
FROM base AS api

EXPOSE ${API_PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD sh -c 'curl -f "http://localhost:${API_PORT}/health" || exit 1'

CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT} --app-dir /app/backend"]

# ---------------------------------------------------------------------------
# Target: streamlit — LanceDB Navigator (configurable via STREAMLIT_PORT)
# ---------------------------------------------------------------------------
FROM base AS streamlit-deps

RUN pip install --no-cache-dir streamlit

FROM streamlit-deps AS streamlit

EXPOSE ${STREAMLIT_PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD sh -c 'curl -f "http://localhost:${STREAMLIT_PORT}/_stcore/health" || exit 1'

CMD ["sh", "-c", "python -m streamlit run backend/scripts/lancedb_navigator.py --server.port=${STREAMLIT_PORT} --server.address=0.0.0.0 --server.headless=true"]

# ---------------------------------------------------------------------------
# Target: calculator — MCP Calculator Server (SSE, configurable via CALCULATOR_PORT)
# ---------------------------------------------------------------------------
FROM base AS calculator

EXPOSE ${CALCULATOR_PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD sh -c 'curl -f "http://localhost:${CALCULATOR_PORT}/health" || exit 1'

CMD ["python", "-m", "advisor_pipeline.mcp_servers.calculator_server.server"]
