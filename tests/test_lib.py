from pathlib import Path
from textwrap import dedent

from manver.lib import (
    Git,
    VersionIdentifier,
    commit_version,
    get_log_til_last_release,
    get_next_version,
    get_projects,
)


def test_bump(mock_project_files):
    path = Path(".manver.test.toml")

    project = get_projects(path)[0]
    # next_vers = [get_next_version(p) for p in projects]
    next_ver = get_next_version(project, VersionIdentifier.AUTO)

    # for next_ver, project in zip(next_vers, projects):
    #     commit_version(project, next_ver)
    commit_version(project, next_ver)

    project2 = get_projects(path)[0]
    # next_vers2 = [p.version for p in projects2]
    next_ver2 = project2.version

    assert next_ver == next_ver2
    assert project.version.next(VersionIdentifier.MINOR) == next_ver

    glog = project.git.log("@^")

    assert "chore: add all" not in glog


def test_get_last_release(mock_project_files):
    msgs = dedent(
        """
        chore: add all
        feat: add Project and next_version
        doc: add version management section to refactor
        chore: use local packages for pre-commit
        feat: change pytoml by tomli
        refactor: change name to `manver`
        doc: proposal for refactor
        release(minor): bump 0.2.0 -> 0.3.0
        """
    ).strip()

    git = Git()
    hashes, msgs2 = get_log_til_last_release(git)

    print(msgs2)

    assert len(msgs.splitlines()) == len(msgs2.splitlines())
    assert len(msgs.splitlines()) == len(hashes.splitlines())
