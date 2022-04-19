from __future__ import annotations

import re
import subprocess
from datetime import datetime
from fileinput import FileInput
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, Optional, TypedDict

import semantic_version
import tomli
from pydantic import BaseModel
from semver import VersionInfo


class FileVersion(BaseModel):
    """Represents a version in a file"""

    file: Path
    version: VersionInfo
    lineno: int
    start_pos: int
    end_pos: int

    class Config:
        arbitrary_types_allowed = True


class FileConfig(BaseModel):
    filename: str
    pattern: str


class VCSConfig(BaseModel):
    commit: bool
    commit_msg: str


class AppConfig(BaseModel):
    filename: str
    config_dict: dict
    files: Dict[str, FileConfig]
    vcs: Optional[VCSConfig]
    path: Path
    current_version: VersionInfo

    class Config:
        arbitrary_types_allowed = True


def save_fileversion(filever: FileVersion):
    """Saves to disk the FileVersion"""

    if not filever.file.is_file():
        raise RuntimeError(f"file={filever.file} is not an actual file")

    start, end = filever.start_pos, filever.end_pos

    with FileInput(files=(filever.file), inplace=True) as f:
        for lineno, line in enumerate(f):
            if lineno == filever.lineno:
                line = line[:start] + str(filever.version) + line[end:]

            print(line, end="")


def init_config() -> str:
    config = dedent(
        """
    # .manver.toml

    [general]
    current_version = ""

    [vcs]
    commit = true
    commit_msg = "release({part}): bump {current_version} -> {new_version}"

    [files]
    """
    ).strip()

    return config


class BaseVCS:
    def __init__(
        self,
        cwd: Path = Path(),
    ):
        self._tag_cmd: list[str] | None

        self.cwd = cwd

    def _run_cmd(self, cmd: list[str], **kwargs):
        """Base function to call any shell command"""
        return subprocess.run(cmd, check=True, cwd=self.cwd, **kwargs)

    def commit(self, msg: str):
        """Commits the changes"""
        cmd = self._get_commit_cmd()
        cmd.append(msg)

        self._run_cmd(cmd)

    def _get_commit_cmd(self) -> list[str]:
        """The formed commit command to pass to subprocess.run

        The last argument is inserted and should be the `commit_msg`
        """
        raise NotImplementedError

    def _is_dirty(self) -> bool:
        raise NotImplementedError

    def check_dirty(self):
        if self._is_dirty():
            raise RuntimeError(
                "The current directory is dirty. Watch out for unstaged files."
            )

    def stage(self, files: list[str]):
        """Stages the files"""
        for file in files:
            self.stage_file(file)

    def stage_file(self, file: str):
        cmd = self._get_stage_cmd()
        cmd.append(file)

        self._run_cmd(cmd)

    def _get_stage_cmd(self) -> list[str]:
        """The formed stage command to pass to subprocess.run

        The last argument is inserted and should be the `filename`
        """
        raise NotImplementedError

    def format_tag_cmd(self, version: str, msg: str):
        """Build the `_tag_cmd` in-place"""

        self._tag_cmd = self._get_tag_cmd(version, msg)

    def tag(self):
        """Tag the version.

        Expected to be run after commit
        """

        cmd = self._tag_cmd

        self._run_cmd(cmd)

    def _get_tag_cmd(self, version: str, msg: str) -> list[str]:
        """The formed tag command to pass to subprocess.run

        Expected to use `version` and `msg`
        """
        raise NotImplementedError


class Git(BaseVCS):
    def _get_commit_cmd(self) -> list[str]:
        return ["git", "commit", "-m"]

    def _get_stage_cmd(self) -> list[str]:
        return ["git", "add"]

    def _is_dirty(self) -> bool:
        cmd = ["git", "status", "--short"]
        p = self._run_cmd(cmd, capture_output=True)

        if p.stdout:
            return True

        return False

    def _get_tag_cmd(self, version: str, msg: str) -> list[str]:
        return ["git", "tag", "-a", version, "-m", msg]

    def get_log(self, start_hash: str):
        p = self._run_cmd(
            ["git", "log", "--oneline", f"{start_hash}..@"], capture_output=True
        )

        return p.stdout.decode("utf8")


class App:
    """The main class

    config_filename: '.manver.toml'
    """

    def __init__(self, config_filename: str = ".manver.toml"):
        # load_config -> verify config in place
        self.config = self.load_config(config_filename)
        self.version = self.config.current_version
        # init vcs if needed
        self.vcs = self._init_vcs()
        # make FileVersions
        self.files_versions = self._init_files_versions()

    def _init_vcs(self) -> BaseVCS | None:
        if not self.config.vcs:
            return None

        # TODO: ability to choose the vcs
        VCSClass = Git

        vcs = VCSClass(cwd=self.config.path)

        # check if not dirty before anything
        vcs.check_dirty()

        return vcs

    def _init_file_version(self, file: str, config: FileConfig) -> FileVersion:
        """Initializes a FileVersion class from a FileConfig"""
        path = self.config.path
        f = path / config.filename

        if not f.is_file():
            raise RuntimeError(
                f"The file '{file}' with filename={f} is not an actual file"
            )

        pattern = re.compile(config.pattern)

        with f.open() as fp:
            for lineno, line in enumerate(fp):
                if match := pattern.search(line):
                    version = match.group(1)
                    # TODO: allow multiple matches per file
                    break

        if not match:
            raise RuntimeError(
                f"The pattern={pattern} did not match on file '{file}'"
                f" with filename={config.filename}"
            )

        version_info = VersionInfo.parse(version)

        if version_info != self.version:
            raise RuntimeError(
                f"The file '{file}' has version '{version_info}' "
                f"but current_version is '{self.version}'"
            )

        start_pos, end_pos = match.span(1)

        return FileVersion(
            file=f,
            version=version_info,
            lineno=lineno,
            start_pos=start_pos,
            end_pos=end_pos,
        )

    def _init_files_versions(self) -> list[FileVersion]:
        """Initializes all the FileVersion's from AppConfig"""
        files_versions: list[FileVersion] = []

        for file, fileconfig in self.config.files.items():
            files_versions.append(self._init_file_version(file, fileconfig))

        return files_versions

    @classmethod
    def load_config(cls, filename: str) -> AppConfig:
        """Load app config"""
        # TODO: specify the path on config
        path = cls._get_path()

        configd = cls._load_config_file(str(path / filename))

        # [files]
        if "files" not in configd:
            raise RuntimeError("Must specify a '[files]'")

        files: dict[str, FileConfig] = {}

        for file, spec in configd["files"].items():
            if "filename" not in spec:
                raise RuntimeError(f"Must specify 'filename' for '{file}'")
            if "pattern" not in spec:
                raise RuntimeError(f"Must specify 'pattern' for '{file}'")

            files[file] = FileConfig(
                filename=spec["filename"],
                pattern=spec["pattern"],
            )

        # save ourselves
        config_pattern = r'current_version *?= *?"(.+?)"'
        files["manver"] = FileConfig(filename=filename, pattern=config_pattern)

        # [vcs]
        vcs = None
        # TODO: decide if we should fail if vcs not specified in config
        if "vcs" in configd:
            vcsd = configd["vcs"]
            if "commit" in vcsd and "commit_msg" in vcsd:
                commit_flag = bool(vcsd["commit"])
                if not commit_flag:
                    raise RuntimeError(
                        "If you do not want to commit, skip the config section."
                        " It is the default behaviour"
                    )
                vcs = VCSConfig(commit=commit_flag, commit_msg=vcsd["commit_msg"])
            elif "commit" in vcsd and "commit_msg" not in vcsd:
                raise RuntimeError(
                    "If `commit` flag is passed, we expect to have a `commit_msg` also"
                )

        # [general]
        if "general" not in configd:
            raise RuntimeError("Must specify '[general]'")

        general = configd["general"]
        if "current_version" not in general:
            raise RuntimeError("Must specify 'current_version' in '[general]'")

        current_version = VersionInfo.parse(general["current_version"])

        return AppConfig(
            filename=filename,
            config_dict=configd,
            files=files,
            path=path,
            vcs=vcs,
            current_version=current_version,
        )

    @staticmethod
    def _get_path() -> Path:
        return Path()

    @staticmethod
    def _load_config_file(
        filename: str,
    ) -> dict[str, Any]:
        """Loads the config from a file"""
        with open(filename, "rb") as f:
            return tomli.load(f)

    def get_commit_msg(self, part: str):
        return self.config.vcs.commit_msg.format(
            part=part,
            current_version=str(self.config.current_version),
            new_version=str(self.version),
        )

    def bump(self, part: str, **kwargs):
        self.version = self.version.next_version(part)

        for filever in self.files_versions:
            filever.version = filever.version.next_version(part, **kwargs)

        if self.vcs:
            cm = self.get_commit_msg(part)

            # TODO: custom tag_msg
            self.vcs.format_tag_cmd(str(self.version), msg=cm)

            return cm

    def auto_bump(self):
        """Automatically bump the version"""
        # TODO: add strategy for which version to bump
        self.bump("minor")

    def save_files(self):
        """Save the files version"""
        for filever in self.files_versions:
            save_fileversion(filever)


class ProjectVersion(TypedDict):
    simple: str
    full: str


class Project:
    def __init__(
        self, name: str, root_dir: str, version: str, version_files: list[str]
    ):
        self.name = name
        self.root_dir = Path(root_dir)
        self.semantic_version = semantic_version.Version(version)
        self.version_files = [Path(s) for s in version_files]

    def next_version(self, identifier: str, last_sha: str) -> "ProjectVersion":
        if identifier == "patch":
            next_version = self.semantic_version.next_patch()
        elif identifier == "minor":
            next_version = self.semantic_version.next_minor()
        elif identifier == "major":
            next_version = self.semantic_version.next_major()

        now = datetime.now()
        simple_version_str = str(next_version)
        next_version.build = (last_sha, f"{now:%Y%m%dT%H%M%SZ}")
        next_version_str = str(next_version)

        return {"simple": simple_version_str, "full": next_version_str}
