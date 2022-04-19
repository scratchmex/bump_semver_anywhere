import subprocess
from pathlib import Path
from shutil import copy
from textwrap import dedent

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def test_files_path(tmp_path):
    from shutil import copytree

    tmp_files = tmp_path / "files"
    test = Path("tests")

    copytree(test / "files", tmp_files)
    copy(
        test / ".manver.test.toml",
        tmp_files / ".manver.toml",
    )

    return tmp_files


@pytest.fixture
def patch_vcs(mocker: MockerFixture):
    from manver.app import BaseVCS

    class FakeProcess:
        stdout = ""

    mocker.patch.object(BaseVCS, "_run_cmd", return_value=FakeProcess)


@pytest.fixture
def patch_app(mocker: MockerFixture, patch_vcs, test_files_path):
    from manver import App

    mocker.patch.object(App, "_get_path", return_value=test_files_path)


@pytest.fixture
def git_repo(tmp_path):
    msgs = dedent(
        """
        fix: execute as script
        fix: entrypoint for gh-action
        chore: add test_version bump and fix test
        feat: add pydantic as the validation lib
        feat: add init command / bump command
        fix: ci gh-action
        fix: bump_semver config for pytest
        release(minor): bump 0.1.2 -> 0.2.0
        docs: update README
        fix: dockerfile install py module
        feat: add tag method to VCS, Git and cli
        release(minor): bump 0.2.0 -> 0.3.0
        doc: proposal for refactor
        refactor: change name to `manver`
        feat: change pytoml by tomli
        chore: use local packages for pre-commit
        doc: add version management section to refactor
        feat: add Project and next_version
    """
    ).strip()

    subprocess.run(["git", "init"], cwd=tmp_path)

    for msg in msgs.split("\n"):
        subprocess.run(["git", "commit", "--allow-empty", "-m", msg], cwd=tmp_path)
