FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml .

COPY sliplane_guide.md sliplane_guide.md

# Install dependencies
RUN uv sync --no-dev

# Copy application code
COPY main.py .

# Run the application
CMD ["uv", "run", "main.py"]
