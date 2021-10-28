from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

import pytomlpp
from attr.setters import frozen
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


@dataclass
class AppConfig:
    config_dict: dict
    files: dict[str, FileConfig]
    path: Path


class App:
    """The main class"""

    def __init__(self):
        # load_config -> verify config in place
        self.config = self.load_config()
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
                f"The pattern={pattern} did not match on file '{file}' with filename={config['filename']}"
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
    def load_config(cls) -> AppConfig:
        """Load app config"""
        configd = cls._load_config_file()

        if not "files" in configd:
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

        path = cls._get_path()

        return AppConfig(config_dict=configd, files=files, path=path)

    @staticmethod
    def _get_path() -> Path:
        return Path()

    @staticmethod
    def _load_config_file(
        filename="bump_semver_anywhere.toml",
    ) -> dict[str, dict[str, dict[str, str]]]:
        """Loads the config from a file. The default name is 'bump_semver_anywhere.toml'"""
        with open(filename) as f:
            return pytomlpp.load(f)

    # def auto_bump():
    #     """Automatically bump the version"""

    # def save_files():
    #     """Save the files version"""
