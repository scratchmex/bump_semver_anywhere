import os
import subprocess
from pathlib import Path
from textwrap import dedent

import pytest


@pytest.fixture
def mock_project_files(tmp_path: Path, request):
    from shutil import copy, copytree

    invocation_dir: Path = request.config.invocation_dir
    test_files = invocation_dir / "tests/files"

    copytree(test_files / "src", tmp_path / "src")
    copy(test_files / ".manver.test.toml", tmp_path)

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

    subprocess.run(["git", "add", "-A"], cwd=tmp_path)
    subprocess.run(["git", "commit", "-m", "chore: add all"], cwd=tmp_path)

    # p = subprocess.run(
    #     ["git", "log", "-n", "1", "--pretty=format:%H", "@^.."],
    #     capture_output=True,
    #     cwd=tmp_path,
    # )
    # last_hash = p.stdout.decode()

    os.chdir(tmp_path)
    yield
    os.chdir(invocation_dir)
