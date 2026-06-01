FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.6 /uv /uvx /bin/

WORKDIR /app

# Prevent bytecode clutter in the image
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Add uv to PATH and configure Python path
ENV PATH="/app/.venv/bin:$PATH"

# Sync dependencies first (layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/

EXPOSE 8000

# Run using the synced venv via uv
CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
