import subprocess

from semver import VersionInfo

from manver import Project, VersionManager
from manver.app import FileVersion, Git


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
