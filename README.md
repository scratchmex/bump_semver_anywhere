# bump semver anywhere

This is a library intented to replace all semversion bumpers and finally be agnostic of the language / use case for your semantic versioning. This is achieved by providing the regex pattern to the place and filename of the string that contains the semantic version.

## usage

- install `pip install bump_semver_anywhere`
- create a `bump_semver_anywhere.toml` in the root of your project (see _config example_)
- run `bump_semver_anywhere -p patch`

### cli

```console
❯ bump_semver_anywhere --help
Usage: bump_semver_anywhere [OPTIONS]

  Bump your semantic version of any software using regex

Options:
  -c, --config FILE               the config file  [default:
                                  bump_semver_anywhere.toml]
  -p, --part [major|minor|patch|prerelease]
                                  the version part to bump  [required]
  -n, --dry-run                   do not modify files
  --help                          Show this message and exit.
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

See `.github/workflows/bump_semver_anywhere.yaml` to integrate the action to your repo and change `uses: ./` to `uses: scratchmex/bump_semver_anywhere@main`

The current behaviour is to comment `/release <part>` (e.g. `/release patch`) in a pull request. 
Per default it pushes the bump commit to the branch the PR points to. 
Therefore it should be commented after accepting the PR