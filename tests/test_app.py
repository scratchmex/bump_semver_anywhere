from __future__ import annotations

import subprocess

from pytest_mock.plugin import MockerFixture
from semver import VersionInfo

from manver import Project, VersionManager
from manver.app import ConventionCommitsStrategy, FileVersion, Git


def test_filever_save_and_bump(patch_version_manager):
    app = VersionManager()

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
            file=path / ".manver.toml",
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
    app_new = VersionManager()

    for file_version in app_new.files_versions:
        assert file_version in exp_files_versions


def test_project():
    proyecto1 = Project(
        name="proyecto1",
        root_dir="app1/src",
        version="1.4.5",
        version_files=["app1/src/__version__.py", "app1/src/docker-compose.yaml"],
    )

    proyecto2 = Project(
        name="proyecto2",
        root_dir="app2/src",
        version="2.0.0-alpha.1",
        version_files=["app2/src/__version__.py", "app2/src/docker-compose.yaml"],
    )

    proy1_bump = proyecto1.next_version(identifier="minor", last_sha="012abcd")
    proy1_bump["simple"] == "2.5.0"
    proy1_bump["full"] == "2.5.0+012abcd.20220101T010101Z"

    proy2_bump = proyecto2.next_version(identifier="major", last_sha="012abcd")
    proy2_bump["simple"] == "2.0.0"
    proy2_bump["full"] == "2.0.0-alpha.1+012abcd.20220101T010101Z"


def test_git_info(tmp_path, git_repo):
    p = subprocess.run(["git", "log", "--oneline"], capture_output=True, cwd=tmp_path)
    log = p.stdout.decode("utf8")
    hashes = [s[:7] for s in log.strip().split("\n")]
    # not included
    last_hash = hashes[-1]
    log_exp = "\n".join(log.strip().split("\n")[:-1]) + "\n"

    git = Git(cwd=tmp_path)

    glog = git.get_log(last_hash)

    assert glog == log_exp

    # test bump strat
    st = ConventionCommitsStrategy(glog)

    assert st.apply() == "minor"


def test_config_load(patch_version_manager):
    app = VersionManager()

    config = app.config

    # [files]
    files = config.files
    assert files

    for x in ["docker", "python-module", "python-pyproject", "javascript"]:
        assert x in files

    for spec in files.values():
        assert spec.filename
        assert spec.pattern

    # [vcs]
    vcs = config.vcs
    commit_msg = "release({part}): bump {current_version} -> {new_version}"

    assert vcs
    assert vcs.commit
    assert vcs.commit_msg == commit_msg

    # [general]
    assert str(app.config.current_version) == "0.1.0"
    assert str(app.version) == "0.1.0"


def test_files_versions(patch_version_manager):
    app = VersionManager()
    path = app.config.path

    version = VersionInfo.parse("0.1.0")
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
            file=path / ".manver.toml",
            version=version,
            lineno=3,
            start_pos=19,
            end_pos=24,
        ),
    ]

    files_versions = app.files_versions

    for file_version in files_versions:
        assert file_version in exp_files_versions


def test_git_stage_and_commit(mocker: MockerFixture, patch_version_manager):
    app = VersionManager()

    assert app.vcs

    cm = app.bump("patch")

    mocked = mocker.patch.object(app.vcs, "_run_cmd", return_value=None)

    app.vcs.stage(app.config.files)

    for file in app.config.files:
        cmd = app.vcs._get_stage_cmd() + [file]
        mocked.assert_any_call(cmd)

    mocked.reset_mock()

    app.vcs.commit(cm)

    mocked.assert_called_once_with(app.vcs._get_commit_cmd() + [cm])
