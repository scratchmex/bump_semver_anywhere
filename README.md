# bump semver anywhere

This is a library intented to replace all semversion bumpers and finally be agnostic of the language / use case for your semantic versioning. This is achieved by providing the regex pattern to the place and filename of the string that contains the semantic version.


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