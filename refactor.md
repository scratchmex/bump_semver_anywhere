# Document for the refactor description of this project

## Name

We need a short name that also reflects what this project is about. After thinking a bit, starting from the idea that this project is for helping managing the versions of projects, agnostic from the language, I ended up with `manver` for [man]agement and [ver]sion.

## Automation

Currently you need to specify which part of the version you want to bump. This is inconvinient when you have many different commits and projects. More over, having the ability to only manage one version for the whole repo is not convenient for monorepo projects.
Because of this, I propose to have automatic identification for the version part to bump via commit messages and also the ability to manage multiple versions for each project. The configuration for each project should include its path to look for commits so it can bump multiple version at the same time and not necessarily the same part.

## CI integration

Currently our integration is to have a command to trigger the bump and commit via Github actions. However, because we propose more automation, it is expected for the CI integration to be more extended. I propose to have one extra point. On each PR the action should make a comment about the auto bump of the version according to that PR. The already manual trigger for the PR should by default be the automatic bump with the option to force a specific bump.

## Version management

Right now we can only manage one global version. For monorepos that is not feasible. Given that motivation the following things are considered in the refactor:
- one repo can have multiple projects each with its own version
- one project can have different files that track the version
- 