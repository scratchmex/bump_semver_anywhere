from pathlib import Path

import pytest
import pytomlpp
from pytest_mock import MockerFixture


@pytest.fixture
def test_config():
    p = Path("tests/bump_semver_anywhere.test.toml")

    return pytomlpp.load(p)


@pytest.fixture
def test_files_path(tmp_path):
    from shutil import copytree

    p = tmp_path / "files"

    copytree(Path("tests/files"), p)

    return p


@pytest.fixture
def patched_app(mocker: MockerFixture, test_config, test_files_path):
    from bump_semver_anywhere import App

    mocker.patch.object(App, "_load_config_file", return_value=test_config)
    mocker.patch.object(App, "_get_path", return_value=test_files_path)

    return App
