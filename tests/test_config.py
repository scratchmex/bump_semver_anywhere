from __future__ import annotations
import re

from pathlib import Path


def test_config_load(config: dict):
    files = config["files"]

    assert files

    for x in ["docker", "python-module", "python-pyproject", "javascript"]:
        assert x in files

    for spec in files.values():
        assert "filename" in spec
        assert "pattern" in spec

        assert spec["filename"]
        assert spec["pattern"]


def test_filename_find(config: dict, files_path: Path):
    files: dict[str, dict[str, str]] = config["files"]

    versions = {
        "docker": "4.2.4",
        "python-module": "1.0.1",
        "python-pyproject": "0.1.0",
        "javascript": "1.0.0",
    }

    for file, spec in files.items():
        filename = spec["filename"]
        patternr = spec["pattern"]

        f = files_path / filename

        assert f.is_file()

        pattern = re.compile(patternr)

        with f.open() as fp:
            for line in fp:
                if match := pattern.search(line):
                    version = match.group(1)
                    assert versions[file] == version
