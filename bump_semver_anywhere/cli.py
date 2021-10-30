from enum import Flag

import click

from .app import App


@click.command()
@click.option(
    "--config",
    default="bump_semver_everywhere.toml",
    show_default=True,
    type=click.Path(exists=True, dir_okay=False),
    help="the config file",
)
@click.option(
    "--part",
    default="patch",
    type=click.Choice(("major", "minor", "patch", "prerelease")),
    show_default=True,
    help="the version part to bump",
)
def main(config, part):
    """The entry point for the cli"""

    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"

    click.secho("[-] Loading config from ", nl=False)
    click.secho(config, fg=BLUE, nl=False)
    click.secho(" and bumping ", nl=False)
    click.secho(part, fg=GREEN)

    app = App(config_filename=config)

    click.secho("[=] config loaded")

    for filever in app.files_versions:
        click.secho(" • ", nl=False)
        click.secho(filever.file, fg=BLUE, nl=False)
        click.secho(": ", nl=False)
        click.secho(filever.version, fg=GREEN)

    click.secho("[-] bumping ", nl=False)
    click.secho(part, fg=GREEN, nl=False)
    click.secho(" version")

    app.bump(part)

    for filever in app.files_versions:
        click.secho(" • ", nl=False)
        click.secho(filever.file, fg=BLUE, nl=False)
        click.secho(" -> ", nl=False)
        click.secho(filever.version, fg=GREEN)

    click.secho("[*] ", nl=False)
    click.secho("saving", fg=CYAN, nl=False)
    click.secho(" files to disk")

    app.save_files()

    click.secho("[+] ", nl=False)
    click.secho("b", fg=RED, nl=False)
    click.secho("y", fg=YELLOW, nl=False)
    click.secho("e ", fg=GREEN, nl=False)
    click.secho("b", fg=CYAN, nl=False)
    click.secho("y", fg=BLUE, nl=False)
    click.secho("e", fg=MAGENTA)


if __name__ == "__main__":
    main()
