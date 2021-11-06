# bump semver anywhere 
[![PyPI version](https://badge.fury.io/py/bump-semver-anywhere.svg)](https://badge.fury.io/py/bump-semver-anywhere)

This is a library intented to replace all semversion bumpers and finally be agnostic of the language / use case for your semantic versioning. This is achieved by providing the regex pattern to the place and filename of the string that contains the semantic version.

## usage

- install `pip install bump_semver_anywhere`
- create a `bump_semver_anywhere.toml` in the root of your project (see _config example_) or run `bump_semver_anywhere init`
- run `bump_semver_anywhere bump -p patch`

```console
Hello there. Today I want to show you a library I have been working on. I was inspired by necessity of changing all the versions in every file: `pyproject.toml`, `__init__.py`, `docker-compose.yaml`, `package.json`, etc. I searched for packages that do this but either they are specific to the language (Python or Javascript) or I did not like the customization for it. At the end I decided to create `bump_semver_anywhere`. This is inspired in [bump2version](https://github.com/c4urself/bump2version/) but with a much simpler approach. It uses TOML for configuration.

> This is a library intended to replace all semantic version bumpers and finally be agnostic of the language. This is achieved by providing the regex pattern to the place and filename of the string that contains the version.

configuration example:
```toml
# bump_semver_anywhere.toml

[general]
current_version = "0.1.2"

[vcs]
commit = true
commit_msg = "release({part}): bump {current_version} -> {new_version}"

[files]

[files.python-module]
filename = "bump_semver_anywhere/__init__.py"
pattern = '__version__ ?= ?"(.*?)"'

[files.python-pyproject]
filename = "pyproject.toml"
pattern = 'version ?= ?"(.*?)"'
```

It can be run as CLI `bump_semver_anywhere bump -p patch` or triggered via a Github action by commenting `/release patch`

```console
❯ python -m bump_semver_anywhere bump -p patch
[-] Loading config from bump_semver_anywhere.toml and bumping patch
[=] config loaded
[ ] files to update
 • bump_semver_anywhere/__init__.py: 0.1.1
 • pyproject.toml: 0.1.1
 • bump_semver_anywhere.toml: 0.1.1
[ ] VCS enabled with git
[-] bumping patch version
 • bump_semver_anywhere/__init__.py -> 0.1.2
 • pyproject.toml -> 0.1.2
 • bump_semver_anywhere.toml -> 0.1.2
[*] saving files to disk
[*] staging
[*] commiting: release(patch): bump 0.1.1 -> 0.1.2
black....................................................................Passed
isort....................................................................Passed
flake8...................................................................Passed
[main 5092515] release(patch): bump 0.1.1 -> 0.1.2
 3 files changed, 3 insertions(+), 3 deletions(-)
[+] bye bye
```


PS: If you have any suggestions for changing the name to a much simpler one I will be grateful.
PS2: I accept PR and any feedback.


### cli

```console
❯ bump_semver_anywhere --help
Usage: python -m bump_semver_anywhere [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  bump  Bump your semantic version of any software using regex
  init  Initialize the config
```

```console
❯ bump_semver_anywhere bump --help
Usage: python -m bump_semver_anywhere bump [OPTIONS]

  Bump your semantic version of any software using regex

Options:
  -c, --config FILE               the config file  [default:
                                  bump_semver_anywhere.toml]
  -p, --part [major|minor|patch|prerelease]
                                  the version part to bump  [required]
  -n, --dry-run                   do not modify files
  --help                          Show this message and exit.
```

```console
❯ bump_semver_anywhere init --help
Usage: python -m bump_semver_anywhere init [OPTIONS]

  Initialize the config

Options:
  -o, --output PATH  the output config file path  [default:
                     bump_semver_anywhere.toml]
  --help             Show this message and exit.
```

## config example

The following example will bump the version for docker and a python or javascript package.

```toml
# bump_semver_anywhere.toml

[general]
current_version = "0.1.0"

[vcs]
commit = true
commit_msg = "release({part}): bump {current_version} -> {new_version}"

[files]

[files.docker]
filename = "docker-compose.yaml"
pattern = 'image:.*?:(.*?)"'

[files.python-module]
filename = "__init__.py"
pattern = '__version__ ?= ?"(.*?)"'

[files.python-pyproject]
filename = "pyproject.toml"
pattern = 'version ?= ?"(.*?)"'

[files.javascript]
filename = "package.json"
pattern = '"version": ?"(.*?)"'
```

## github action

See `.github/workflows/bump_semver_anywhere.yaml` to integrate the action to your repo.

The current behaviour is to comment `/release <part>` (e.g. `/release patch`) in a pull request. 
Per default it pushes the bump commit to the branch the PR points to. 
Therefore it should be commented after accepting the PR