FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

COPY sliplane_guide.md sliplane_guide.md
COPY sliplane_preset_guide.md sliplane_preset_guide.md
COPY sliplane_presets.json sliplane_presets.json

# Install dependencies (locked to exact versions)
RUN uv sync --no-dev --frozen

# Copy application code
COPY main.py origin_lock.py preset_guide.py tool_annotations.py ./

# Run the application
CMD ["uv", "run", "main.py"]
