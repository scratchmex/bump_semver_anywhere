from __future__ import annotations

import re
from pathlib import Path

from semver import VersionInfo

from bump_semver_anywhere import App
from bump_semver_anywhere.app import FileVersion


def test_config_load(patched_app):
    app: App = patched_app()

    config = app.config
    files = config.files

    assert files

    for x in ["docker", "python-module", "python-pyproject", "javascript"]:
        assert x in files

    for spec in files.values():
        assert "filename" in spec
        assert "pattern" in spec

        assert spec["filename"]
        assert spec["pattern"]


def test_files_versions(patched_app):
    app: App = patched_app()

    exp_files_versions = [
        FileVersion(
            file=Path("tests/files/docker-compose.yaml"),
            version=VersionInfo.parse("4.2.4"),
            lineno=5,
            start_pos=22,
            end_pos=27,
        ),
        FileVersion(
            file=Path("tests/files/package.json"),
            version=VersionInfo.parse("1.0.0"),
            lineno=2,
            start_pos=16,
            end_pos=21,
        ),
        FileVersion(
            file=Path("tests/files/__init__.py"),
            version=VersionInfo.parse("1.0.1"),
            lineno=0,
            start_pos=15,
            end_pos=20,
        ),
        FileVersion(
            file=Path("tests/files/pyproject.toml"),
            version=VersionInfo.parse("0.1.0"),
            lineno=2,
            start_pos=11,
            end_pos=16,
        ),
    ]

    files_versions = app.files_versions

    for file_version in files_versions:
        assert file_version in exp_files_versions
