from pathlib import Path

from manver.lib import VersionIdentifier, commit_version, get_next_version, get_projects


def test_bump(mock_project_files):
    path = Path(".manver.test.toml")

    project = get_projects(path)[0]
    # next_vers = [get_next_version(p) for p in projects]
    next_ver = get_next_version(project)

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
