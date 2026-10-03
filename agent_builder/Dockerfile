FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies (curl for healthchecks, git for tool installs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# ── Layer 1: Dependencies (cached unless pyproject.toml changes) ──
COPY pyproject.toml uv.lock ./

RUN uv venv /app/.venv && \
    uv pip install --no-cache-dir .

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# ── Layer 2: Project files (changes frequently) ──
COPY agents/ ./agents/
COPY crew.jsonc ./
COPY README.md ./
COPY tools/ ./tools/
COPY knowledge/ ./knowledge/
COPY skills/ ./skills/
COPY *.py ./

# Verify installation
RUN crewai --version

# Default entrypoint — overridable per run
CMD ["crewai", "run"]