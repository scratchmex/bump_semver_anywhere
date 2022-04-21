from __future__ import annotations

import enum
import re
import subprocess
from pathlib import Path
from textwrap import dedent

import semantic_version
import tomli
from pydantic import BaseModel


class VersionIdentifier(enum.Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"
    AUTO = "auto"


class FileConfig(BaseModel):
    path: Path
    pattern: str


class ProjectConfig(BaseModel):
    name: str
    version: str
    files: list[FileConfig]
    bump_strategy: str
    commit_msg_tpl: str


class Config(BaseModel):
    commit_msg_tpl: str
    bump_strategy: str
    projects: list[ProjectConfig]


class FileVersion:
    def __init__(self, path: str, pattern: str) -> None:
        self.path = Path(path)
        self.pattern = re.compile(pattern)

        self._content = self._load_file()
        self._match = self.pattern.search(self._content)

        if not self._match:
            raise ValueError(f"the pattern {pattern!r} did not match in {path!s}")

    def __repr__(self) -> str:
        return f"FileVersion(path={self.path!r}, pattern={self.pattern!r})"
        # <match={self._match!r}>

    def _load_file(self):
        return self.path.read_text("utf8")

    def _save_file(self, content: str):
        self.path.write_text(content, "utf8")

    def update(self, version: str):
        start, end = self._match.span(1)
        content = self._content[:start] + version + self._content[end:]

        self._save_file(content)


class ProjectVersion:
    def __init__(self, version: str) -> None:
        self._version = semantic_version.Version(version)

    def __repr__(self):
        return repr(self._version)

    def __str__(self):
        return str(self._version)

    def __eq__(self, other):
        if isinstance(other, ProjectVersion):
            return self._version.__eq__(other._version)

        return self._version.__eq__(other)

    @property
    def identifier(self):
        # TODO: add prerelrease
        if self._version.patch != 0:
            return VersionIdentifier.PATCH
        elif self._version.minor != 0:
            return VersionIdentifier.MINOR
        elif self._version.major != 0:
            return VersionIdentifier.MAJOR

    def next(self, identifier: VersionIdentifier) -> "ProjectVersion":
        _version = self._version

        print(f"{identifier=}")

        if identifier == VersionIdentifier.MAJOR:
            version = _version.next_major()
        elif identifier == VersionIdentifier.MINOR:
            version = _version.next_minor()
        elif identifier == VersionIdentifier.PATCH:
            version = _version.next_patch()
        else:
            # TODO: support prerelease
            raise NotImplementedError

        return ProjectVersion(str(version))


class Git:
    def __init__(self, cwd: Path | None = None) -> None:
        self._cwd = cwd or Path()

    def __repr__(self) -> str:
        return repr(self.__dict__)

    def _run_cmd(self, cmd: list[str], **kwargs):
        """Base function to call any shell command"""
        try:
            p = subprocess.run(cmd, check=True, cwd=self._cwd, **kwargs)
        except subprocess.CalledProcessError as e:
            print(f"{e.stderr=}")
            print(f"{e.stdout=}")
            raise

        return p

    def last_commit_hash_updated_files(self, files: list[Path]) -> str:
        cmd = ["git", "log", "--oneline", "--"]

        for file in files:
            cmd.append(str(file))

        p = self._run_cmd(cmd, capture_output=True)

        out = p.stdout
        if isinstance(out, bytes):
            out = out.decode("utf8").strip()

        if not out:
            raise RuntimeError("no git history")

        # FIXME: avoid hardcoding this
        match = re.search(r"^release", out, re.MULTILINE)
        if not match:
            last_hash = out.strip().split("\n")[-1]
        else:
            last_hash = match.group()
        last_hash = last_hash[:7]

        return last_hash

    def log(self, start_hash: str | None = None):

        cmd = ["git", "log", "--oneline"]
        if start_hash:
            cmd.append(f"{start_hash}..@")
        p = self._run_cmd(cmd, capture_output=True)
        out = p.stdout
        if isinstance(out, bytes):
            out = out.decode("utf8").strip()

        if not out:
            raise RuntimeError("no git history")

        return out.strip()

    def stage_files(self, files: list[Path]):
        cmd = ["git", "add", "--"]

        for file in files:
            cmd.append(str(file))

        self._run_cmd(cmd)

    def is_dirty(self) -> bool:
        p = self._run_cmd(["git", "status", "--short"], capture_output=True)

        if p.stdout:
            return True

        return False

    def commit(self, msg: str):
        self._run_cmd(["git", "commit", "-m", msg])


class Project:
    def __init__(self, git: Git, config: ProjectConfig) -> None:
        self.name = config.name
        self.git = git
        self.files = [FileVersion(f.path, f.pattern) for f in config.files]
        self.version = ProjectVersion(config.version)
        self.bump_strategy = config.bump_strategy
        self.commit_msg_tpl = config.commit_msg_tpl
        self._config = config

    def __repr__(self) -> str:
        return (
            f"Project(git={self.git!r}, version={self.version!r}, files={self.files!r})"
        )


class VersionBumpStrategy:
    _cc_minor_re = re.compile(r"^\w{7} feat", re.MULTILINE)
    _cc_major_re = re.compile(r"^\w{7} [\w()]+!:", re.MULTILINE)

    def __init__(self, commit_log: str) -> None:
        self.commit_log = commit_log

    def _conventional_commits(self):
        if not self.commit_log:
            raise RuntimeError("no commit log")

        if self._cc_major_re.search(self.commit_log):
            return VersionIdentifier.MAJOR

        if self._cc_minor_re.search(self.commit_log):
            return VersionIdentifier.MINOR

        return VersionIdentifier.PATCH

    def apply(self, strat: str) -> VersionIdentifier:
        if strat == "conventional_commits":
            return self._conventional_commits()

        raise NotImplementedError


def load_config(path: Path | None = None) -> Config:
    if not path:
        path = Path(".manver.toml")

    with open(path, "rb") as f:
        config_dict = tomli.load(f)

    root_path = path.parent
    projects = []
    for p_name, pcd in config_dict["projects"].items():
        files = [
            FileConfig(path=root_path / fc["path"], pattern=fc["pattern"])
            for fc in pcd["files"]
        ]
        # save ourselves
        files.append(
            FileConfig(
                path=root_path / path.name,
                pattern=r'version *?= *?"(.+?)" *?#: ?' + p_name,
            )
        )

        projects.append(
            ProjectConfig(
                name=p_name,
                version=pcd["version"],
                files=files,
                commit_msg_tpl=config_dict["commit_msg_tpl"],
                bump_strategy=config_dict["bump_strategy"],
            )
        )

    return Config(
        commit_msg_tpl=config_dict["commit_msg_tpl"],
        bump_strategy=config_dict["bump_strategy"],
        projects=projects,
    )


def get_projects(path: Path | None = None) -> list[Project]:
    if path:
        config = load_config(path)
        git = Git(cwd=path.parent)
    else:
        config = load_config()
        git = Git()

    return [Project(git=git, config=pc) for pc in config.projects]


def get_next_version(project: Project, part: VersionIdentifier) -> ProjectVersion:
    if part != VersionIdentifier.AUTO:
        return project.version.next(part)

    last_hash = project.git.last_commit_hash_updated_files(
        [f.path for f in project.files]
    )
    git_log = project.git.log(start_hash=last_hash)
    part = VersionBumpStrategy(git_log).apply(project.bump_strategy)

    return project.version.next(part)


def commit_version(project: Project, next_project_version: ProjectVersion):
    next_project_version_str = str(next_project_version)
    commit_msg = project.commit_msg_tpl.format(
        prev_version=str(project.version),
        next_version=next_project_version_str,
        name=project.name,
        identifier=next_project_version.identifier.value,
    )

    for fv in project.files:
        fv.update(next_project_version_str)

    project.git.stage_files([f.path for f in project.files])
    project.git.commit(commit_msg)

    # TODO: add tag
    # git.tag(f"{project.name}-{next_project_version_str}")


def init_config() -> str:
    return dedent(
        """
bump_strategy = "conventional_commits"
commit_msg_tpl = "release({identifier}): bump {name} {prev_version} -> {next_version}"

[projects.test-project]
version = "0.1.0"  #: test-project

files = [
{path = "src/__init__.py", pattern = '__version__ ?= ?"(.*?)"'},
{path = "src/pyproject.toml", pattern = 'version ?= ?"(.*?)"'},
{path = "src/package.json", pattern = '"version": ?"(.*?)"'},
{path = "src/docker-compose.yaml", pattern = 'image:.*?:(.*?)"'},
]
    """
    ).strip()
