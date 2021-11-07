from pathlib import Path

import click

from .app import App, init_config

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
    default="bump_semver_anywhere.toml",
    show_default=True,
    type=click.Path(exists=True, dir_okay=False),
    help="the config file",
)
@click.option(
    "--part",
    "-p",
    required=True,
    type=click.Choice(("major", "minor", "patch", "prerelease")),
    show_default=True,
    help="the version part to bump",
)
@click.option(
    "--dry-run",
    "-n",
    flag_value=True,
    help="do not modify files",
)
def bump(config: str, part: str, dry_run: bool):
    """Bump your semantic version of any software using regex"""

    if dry_run:
        click.secho("[!] ", nl=False)
        click.secho("Dry run", fg=RED)

    click.secho("[-] Loading config from ", nl=False)
    click.secho(config, fg=BLUE, nl=False)
    click.secho(" and bumping ", nl=False)
    click.secho(part, fg=GREEN)

    app = App(config_filename=config)

    click.secho("[=] config loaded")

    click.secho("[ ] files to update")
    for filever in app.files_versions:
        click.secho(" • ", nl=False)
        click.secho(filever.file, fg=BLUE, nl=False)
        click.secho(": ", nl=False)
        click.secho(filever.version, fg=GREEN)

    if app.vcs:
        click.secho("[ ] VCS ", nl=False)
        click.secho("enabled", fg=CYAN, nl=False)
        click.secho(" with ", nl=False)
        click.secho(app.vcs.__class__.__name__.lower(), fg=GREEN)

    click.secho("[-] bumping ", nl=False)
    click.secho(part, fg=GREEN, nl=False)
    click.secho(" version")

    app.bump(part)

    for filever in app.files_versions:
        click.secho(" • ", nl=False)
        click.secho(filever.file, fg=BLUE, nl=False)
        click.secho(" -> ", nl=False)
        click.secho(filever.version, fg=GREEN)

    if not dry_run:
        click.secho("[*] ", nl=False)
        click.secho("saving", fg=CYAN, nl=False)
        click.secho(" files to disk")

        app.save_files()

    if not dry_run and app.vcs:
        click.secho("[*] ", nl=False)
        click.secho("staging", fg=CYAN)

        app.vcs.stage()

        click.secho("[*] ", nl=False)
        click.secho("commiting", fg=CYAN, nl=False)
        click.secho(": ", nl=False)
        click.secho(app.vcs.commit_msg, fg=GREEN)

        app.vcs.commit()

        click.secho("[*] ", nl=False)
        click.secho("tagging", fg=CYAN)

        app.vcs.tag()

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
    default="bump_semver_anywhere.toml",
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
