import json
from pathlib import Path


BASE_DIR = Path(__file__).parent
GUIDE = BASE_DIR.joinpath("sliplane_preset_guide.md").read_text(encoding="utf-8")
PRESETS = json.loads(
    BASE_DIR.joinpath("sliplane_presets.json").read_text(encoding="utf-8")
)


def _preset_id(preset: dict) -> str:
    return preset["settings"]["presetId"]


def _catalog() -> str:
    rows = [f"- `{_preset_id(preset)}` — {preset['name']}" for preset in PRESETS]
    return "## Available preset IDs\n\n" + "\n".join(rows)


def get_preset_guide(preset_id: str | None = None) -> str:
    """Return preset deployment instructions and optionally preset settings."""
    if preset_id is None or not preset_id.strip():
        return f"{GUIDE.rstrip()}\n\n{_catalog()}\n"

    query = preset_id.strip().casefold()
    if query == "all":
        payload = PRESETS
        heading = "All preset settings"
    else:
        payload = next(
            (
                preset
                for preset in PRESETS
                if query
                in {_preset_id(preset).casefold(), preset["name"].casefold()}
            ),
            None,
        )
        if payload is None:
            available = ", ".join(_preset_id(preset) for preset in PRESETS)
            return f"Unknown preset {preset_id!r}. Available preset IDs: {available}"
        heading = f"Preset settings: {_preset_id(payload)}"

    settings = json.dumps(payload, indent=2, ensure_ascii=False)
    return f"{GUIDE.rstrip()}\n\n## {heading}\n\n```json\n{settings}\n```\n"
