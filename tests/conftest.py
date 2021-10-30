from pathlib import Path
from shutil import copy

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def test_files_path(tmp_path):
    from shutil import copytree

    tmp_files = tmp_path / "files"
    test = Path("tests")

    copytree(test / "files", tmp_files)
    copy(
        test / "bump_semver_anywhere.test.toml",
        tmp_files / "bump_semver_anywhere.toml",
    )

    return tmp_files


@pytest.fixture
def patch_vcs(mocker: MockerFixture):
    from bump_semver_anywhere.app import BaseVCS

    class FakeProcess:
        stdout = ""

    mocker.patch.object(BaseVCS, "_run_cmd", return_value=FakeProcess)


@pytest.fixture
def patch_app(mocker: MockerFixture, patch_vcs, test_files_path):
    from bump_semver_anywhere import App

    mocker.patch.object(App, "_get_path", return_value=test_files_path)
