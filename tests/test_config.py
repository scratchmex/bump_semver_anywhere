from __future__ import annotations

from semver import VersionInfo

from manver import App
from manver.app import FileVersion


def test_config_load(patch_app):
    app = App()

    config = app.config

    # [files]
    files = config.files
    assert files

    for x in ["docker", "python-module", "python-pyproject", "javascript"]:
        assert x in files

    for spec in files.values():
        assert spec.filename
        assert spec.pattern

    # [vcs]
    vcs = config.vcs
    commit_msg = "release({part}): bump {current_version} -> {new_version}"

    assert vcs
    assert vcs.commit
    assert vcs.commit_msg == commit_msg

    # [general]
    assert str(app.config.current_version) == "0.1.0"
    assert str(app.version) == "0.1.0"


def test_files_versions(patch_app):
    app = App()
    path = app.config.path

    version = VersionInfo.parse("0.1.0")
    exp_files_versions = [
        FileVersion(
            file=path / "docker-compose.yaml",
            version=version,
            lineno=5,
            start_pos=22,
            end_pos=27,
        ),
        FileVersion(
            file=path / "package.json",
            version=version,
            lineno=2,
            start_pos=16,
            end_pos=21,
        ),
        FileVersion(
            file=path / "__init__.py",
            version=version,
            lineno=0,
            start_pos=15,
            end_pos=20,
        ),
        FileVersion(
            file=path / "pyproject.toml",
            version=version,
            lineno=2,
            start_pos=11,
            end_pos=16,
        ),
        FileVersion(
            file=path / ".manver.toml",
            version=version,
            lineno=3,
            start_pos=19,
            end_pos=24,
        ),
    ]

    files_versions = app.files_versions

    for file_version in files_versions:
        assert file_version in exp_files_versions
