from __future__ import annotations

from semver import VersionInfo

from bump_semver_anywhere import App
from bump_semver_anywhere.app import FileVersion


def test_config_load(patch_app):
    app = App()

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

    vcs = config.vcs
    commit_msg = "release({part}): bump {current_version} -> {new_version}"

    assert vcs
    assert vcs["commit"]
    assert vcs["commit_msg"] == commit_msg

    assert app.vcs.commit_msg == commit_msg
    for file in files.values():
        assert file["filename"] in app.vcs.files


def test_files_versions(patch_app):
    app = App()
    path = app.config.path

    exp_files_versions = [
        FileVersion(
            file=path / "docker-compose.yaml",
            version=VersionInfo.parse("4.2.4"),
            lineno=5,
            start_pos=22,
            end_pos=27,
        ),
        FileVersion(
            file=path / "package.json",
            version=VersionInfo.parse("1.0.0"),
            lineno=2,
            start_pos=16,
            end_pos=21,
        ),
        FileVersion(
            file=path / "__init__.py",
            version=VersionInfo.parse("1.0.1"),
            lineno=0,
            start_pos=15,
            end_pos=20,
        ),
        FileVersion(
            file=path / "pyproject.toml",
            version=VersionInfo.parse("0.1.0"),
            lineno=2,
            start_pos=11,
            end_pos=16,
        ),
    ]

    files_versions = app.files_versions

    for file_version in files_versions:
        assert file_version in exp_files_versions
