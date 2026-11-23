FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

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
