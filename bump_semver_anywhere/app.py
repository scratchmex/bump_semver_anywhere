from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from fileinput import FileInput
from pathlib import Path
from typing import Any, TypedDict

import pytomlpp
from semver import VersionInfo


@dataclass
class FileVersion:
    """Represents a version in a file"""

    file: Path
    version: VersionInfo
    lineno: int
    start_pos: int
    end_pos: int


class FileConfig(TypedDict):
    filename: str
    pattern: str


class VCSConfig(TypedDict):
    commit: bool
    commit_msg: str


@dataclass
class AppConfig:
    filename: str
    config_dict: dict
    files: dict[str, FileConfig]
    vcs: VCSConfig | None
    path: Path
    current_version: VersionInfo


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


class BaseVCS:
    def __init__(self, commit_msg: str, files: list[str], cwd: Path):
        self.commit_msg = commit_msg
        self.commit_msg_fmtd = False
        self.files = files
        self.cwd = cwd

    def _run_cmd(self, cmd: list[str], **kwargs):
        """Base function to call any shell command"""
        return subprocess.run(cmd, check=True, cwd=self.cwd, **kwargs)

    def format_commit_msg(self, part: str, curr_version: str, new_version: str):
        """Formats the `commit_msg` template in-place"""

        fmtd = self.commit_msg.format(
            part=part, current_version=curr_version, new_version=new_version
        )

        self.commit_msg = fmtd
        self.commit_msg_fmtd = True

    def commit(self):
        """Commits the changes"""
        if not self.commit_msg_fmtd:
            raise RuntimeError("You need to call `format_commit_msg` before commiting")

        cmd = self._get_commit_cmd()
        cmd.append(self.commit_msg)

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

    def stage(self):
        """Stages the files"""
        for file in self.files:
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


class App:
    """The main class

    config_filename: 'bump_semver_anywhere.toml'
    """

    def __init__(self, config_filename: str = "bump_semver_anywhere.toml"):
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

        vcs = VCSClass(
            commit_msg=self.config.vcs["commit_msg"],
            files=[file["filename"] for file in self.config.files.values()],
            cwd=self.config.path,
        )

        # check if not dirty before anything
        vcs.check_dirty()

        return vcs

    def _init_file_version(self, file: str, config: FileConfig) -> FileVersion:
        """Initializes a FileVersion class from a FileConfig"""
        path = self.config.path
        f = path / config["filename"]

        if not f.is_file():
            raise RuntimeError(
                f"The file '{file}' with filename={f} is not an actual file"
            )

        pattern = re.compile(config["pattern"])

        with f.open() as fp:
            for lineno, line in enumerate(fp):
                if match := pattern.search(line):
                    version = match.group(1)
                    # TODO: allow multiple matches per file
                    break

        if not match:
            raise RuntimeError(
                f"The pattern={pattern} did not match on file '{file}'"
                f" with filename={config['filename']}"
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
        files["bump_semver_anywhere"] = FileConfig(
            filename=filename, pattern=config_pattern
        )

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
        with open(filename) as f:
            return pytomlpp.load(f)

    def bump(self, part: str, **kwargs):
        self.version = self.version.next_version(part)

        for filever in self.files_versions:
            filever.version = filever.version.next_version(part, **kwargs)

        if self.vcs:
            self.vcs.format_commit_msg(
                part=part,
                curr_version=str(self.config.current_version),
                new_version=str(self.version),
            )

    def auto_bump(self):
        """Automatically bump the version"""
        # TODO: add strategy for which version to bump
        self.bump("minor")

    def save_files(self):
        """Save the files version"""
        for filever in self.files_versions:
            save_fileversion(filever)
