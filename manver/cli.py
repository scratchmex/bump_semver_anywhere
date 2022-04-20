from pathlib import Path

import click

from .lib import (
    VersionIdentifier,
    commit_version,
    get_next_version,
    get_projects,
    init_config,
)

RED = "red"
GREEN = "green"
YELLOW = "yellow"
BLUE = "blue"
MAGENTA = "magenta"
CYAN = "cyan"


@click.group()
def main():
    pass


@main.command()
@click.option(
    "--config",
    "-c",
    default=".manver.toml",
    show_default=True,
    type=click.Path(exists=True, dir_okay=False),
    help="the config file",
)
@click.option(
    "--id",
    "-i",
    required=False,
    type=click.Choice(VersionIdentifier._value2member_map_),
    show_default=True,
    default=VersionIdentifier.AUTO.value,
    help="the version identifier to bump",
)
@click.option(
    "--yes",
    "-y",
    flag_value=True,
    default=False,
    help="accept the changes",
)
def bump(config: Path, id: str, yes: bool):
    """Bump your semantic version of any software using regex"""

    if yes:
        click.secho("[!] ", nl=False)
        click.secho("auto commiting", fg=RED)

    click.secho("[-] loading config from ", nl=False)
    click.secho(config, fg=BLUE, nl=False)
    click.secho("...", nl=False)

    projects = get_projects(Path(config))

    click.secho("done", fg=GREEN)

    click.secho("[-] bumping ", nl=False)
    click.secho(id, fg=CYAN, nl=False)
    click.secho("...", nl=False)

    next_vers = [
        get_next_version(p, VersionIdentifier._value2member_map_[id]) for p in projects
    ]

    click.secho("done", fg=GREEN)

    for next_ver, project in zip(next_vers, projects):
        click.secho(f"[=] {project.name!s} project ", nl=False)
        click.secho(project.version, fg=MAGENTA, nl=False)
        click.secho(" -> ", nl=False)
        click.secho(next_ver, fg=GREEN)

        for file in project.files:
            click.secho(f" •  {file.path!s}")

    if not yes:
        if click.confirm("[?] do you want to commit the versions?", default=False):
            yes = True

    if yes:
        click.secho("[*] ", nl=False)
        click.secho("commiting", fg=CYAN, nl=False)
        click.secho(" version...", nl=False)

        for next_ver, project in zip(next_vers, projects):
            commit_version(project, next_ver)

        click.secho("done", fg=GREEN)

    click.secho("[+] ", nl=False)
    click.secho("b", fg=RED, nl=False)
    click.secho("y", fg=YELLOW, nl=False)
    click.secho("e ", fg=GREEN, nl=False)
    click.secho("b", fg=CYAN, nl=False)
    click.secho("y", fg=BLUE, nl=False)
    click.secho("e", fg=MAGENTA)


@main.command()
@click.option(
    "--output",
    "-o",
    default=".manver.toml",
    show_default=True,
    type=click.Path(path_type=Path),
    help="the output config file path",
)
def init(output: Path):
    """Initialize the config"""
    if output.suffix != ".toml":
        click.secho("[!] output needs to have a toml extension", fg=YELLOW)
        return

    if output.exists():
        click.secho(f"[!] the file {output} already exists. Exiting", fg=RED)
        return

    with open(output, "w") as f:
        config = init_config()
        f.write(config)


if __name__ == "__main__":
    main()
