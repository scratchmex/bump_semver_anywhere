from semver import VersionInfo

from bump_semver_anywhere import App
from bump_semver_anywhere.app import FileVersion


def test_filever_save_and_bump(patch_app):
    app = App()

    app.bump("patch")

    path = app.config.path

    exp_files_versions = [
        FileVersion(
            file=path / "docker-compose.yaml",
            version=VersionInfo.parse("4.2.5"),
            lineno=5,
            start_pos=22,
            end_pos=27,
        ),
        FileVersion(
            file=path / "package.json",
            version=VersionInfo.parse("1.0.1"),
            lineno=2,
            start_pos=16,
            end_pos=21,
        ),
        FileVersion(
            file=path / "__init__.py",
            version=VersionInfo.parse("1.0.2"),
            lineno=0,
            start_pos=15,
            end_pos=20,
        ),
        FileVersion(
            file=path / "pyproject.toml",
            version=VersionInfo.parse("0.1.1"),
            lineno=2,
            start_pos=11,
            end_pos=16,
        ),
    ]

    for file_version in app.files_versions:
        assert file_version in exp_files_versions

    # save files to disk
    app.save_files()

    # test re-read
    app_new = App()

    for file_version in app_new.files_versions:
        assert file_version in exp_files_versions
