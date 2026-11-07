"""Guard against the image missing files the app needs at runtime.

Unit tests run from the repo checkout where every file exists, so a module
left out of the Dockerfile's COPY lines only fails once deployed. This test
follows main.py's local imports and the data files those modules read, and
checks each one is copied into the image.
"""

import ast
import shlex
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_SUFFIXES = (".md", ".json")


def _copied_files() -> set[str]:
    copied = set()
    for line in ROOT.joinpath("Dockerfile").read_text().splitlines():
        parts = shlex.split(line)
        if parts and parts[0].upper() == "COPY" and not any(
            p.startswith("--from") for p in parts
        ):
            copied.update(parts[1:-1])
    return copied


def _runtime_files(entrypoint: str = "main.py") -> set[str]:
    """Local modules reachable from the entrypoint, plus data files they name."""
    needed, pending = set(), [entrypoint]
    while pending:
        name = pending.pop()
        if name in needed:
            continue
        needed.add(name)
        tree = ast.parse(ROOT.joinpath(name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules = [node.module]
            elif (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value.endswith(DATA_SUFFIXES)
                and ROOT.joinpath(node.value).is_file()
            ):
                needed.add(node.value)
                continue
            else:
                continue
            for module in modules:
                path = f"{module.split('.')[0]}.py"
                if ROOT.joinpath(path).is_file():
                    pending.append(path)
    return needed


class DockerfileTest(unittest.TestCase):
    def test_runtime_files_are_copied_into_image(self):
        runtime = _runtime_files()
        self.assertTrue({"main.py", "tool_annotations.py"} <= runtime, runtime)
        missing = sorted(runtime - _copied_files())
        self.assertEqual(missing, [], f"Not copied by Dockerfile: {missing}")


if __name__ == "__main__":
    unittest.main()
