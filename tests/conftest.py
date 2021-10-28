import pytomlpp
import pytest

from textwrap import dedent


config_toml = dedent(
    """
    # bump_semver_anywhere.toml
    [files]

    [files.docker]
    filename = "docker-compose.yaml"
    pattern = 'image:.*?:(.*?)"'

    [files.python-module]
    filename = "__init__.py"
    pattern = "__version__ ?= ?'(.*?)'"

    [files.python-pyproject]
    filename = "pyproject.toml"
    pattern = 'version ?= ?"(.*?)"'

    [files.javascript]
    filename = "package.json"
    pattern = '"version": ?"(.*?)"'
"""
)


@pytest.fixture
def config():
    return pytomlpp.loads(config_toml)
