from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import pytest
import pytomlpp
from pytest_mock import MockerFixture

config_toml = dedent(
    """
    # bump_semver_anywhere.toml
    [files]

    [files.docker]
    filename = "docker-compose.yaml"
    pattern = 'image:.*?:(.*?)"'

    [files.python-module]
    filename = "__init__.py"
    pattern = '__version__ ?= ?"(.*?)"'

    [files.python-pyproject]
    filename = "pyproject.toml"
    pattern = 'version ?= ?"(.*?)"'

    [files.javascript]
    filename = "package.json"
    pattern = '"version": ?"(.*?)"'
"""
)


@pytest.fixture
def test_config():
    return pytomlpp.loads(config_toml)


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
