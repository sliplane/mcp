"""Guard against the image missing files the app needs at runtime.

Unit tests run from the repo checkout where every file exists, so a module
left out of the Dockerfile's COPY lines only fails once deployed.
"""

import fnmatch
import shlex
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _copied_patterns() -> list[str]:
    patterns = []
    for line in ROOT.joinpath("Dockerfile").read_text().splitlines():
        parts = shlex.split(line)
        if parts and parts[0].upper() == "COPY" and not any(
            p.startswith("--from") for p in parts
        ):
            patterns.extend(parts[1:-1])
    return patterns


class DockerfileTest(unittest.TestCase):
    def test_runtime_files_are_copied_into_image(self):
        patterns = _copied_patterns()
        required = [p.name for p in ROOT.glob("*.py")]
        required += [p.name for p in ROOT.glob("sliplane_*") if p.is_file()]
        missing = [
            name
            for name in required
            if not any(fnmatch.fnmatch(name, pattern) for pattern in patterns)
        ]
        self.assertEqual(missing, [], f"Not copied by Dockerfile: {missing}")


if __name__ == "__main__":
    unittest.main()
