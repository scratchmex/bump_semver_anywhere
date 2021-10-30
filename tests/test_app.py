from semver import VersionInfo

from bump_semver_anywhere import App
from bump_semver_anywhere.app import FileVersion


def test_filever_save_and_bump(patch_app):
    app = App()

    PART = "patch"

    app.bump(PART)

    path = app.config.path

    version = VersionInfo.parse("0.1.1")
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
            file=path / "bump_semver_anywhere.toml",
            version=version,
            lineno=3,
            start_pos=19,
            end_pos=24,
        ),
    ]

    assert app.config.current_version.next_version(PART) == app.version

    for file_version in app.files_versions:
        assert file_version in exp_files_versions

    # save files to disk
    app.save_files()

    # test re-read
    app_new = App()

    for file_version in app_new.files_versions:
        assert file_version in exp_files_versions
