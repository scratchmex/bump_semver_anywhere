from __future__ import annotations

import re
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
    config_dict: dict
    files: dict[str, FileConfig]
    vcs: VCSConfig | None
    path: Path


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


class App:
    """The main class

    config_filename: 'bump_semver_anywhere.toml'
    """

    def __init__(self, config_filename: str = "bump_semver_anywhere.toml"):
        # load_config -> verify config in place
        self.config = self.load_config(config_filename)
        # make FileVersions
        self.files_versions = self._init_files_versions()

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

        start_pos, end_pos = match.span(1)

        return FileVersion(
            file=f,
            version=version_info,
            lineno=lineno,
            start_pos=start_pos,
            end_pos=end_pos,
        )

    def _init_files_versions(self) -> list[FileVersion]:
        """Ïnitializes all the FileVersion's from AppConfig"""
        files_versions: list[FileVersion] = []

        for file, fileconfig in self.config.files.items():
            files_versions.append(self._init_file_version(file, fileconfig))

        return files_versions

    @classmethod
    def load_config(cls, filename: str) -> AppConfig:
        """Load app config"""
        configd = cls._load_config_file(filename)

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

        # TODO: specify the path on config
        path = cls._get_path()

        # TODO: add ability to normalize version by having a `current_version` field
        #       on the config to panic if the versions do not coincide

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

        return AppConfig(config_dict=configd, files=files, path=path, vcs=vcs)

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
        for filever in self.files_versions:
            filever.version = filever.version.next_version(part, **kwargs)

    def auto_bump(self):
        """Automatically bump the version"""
        # TODO: add strategy for which version to bump
        self.bump("minor")

    def save_files(self):
        """Save the files version"""
        for filever in self.files_versions:
            save_fileversion(filever)
