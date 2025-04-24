# trying out typer from my friend sebastain
import typer
from apsimNGpy.core_utils.utils import timer
from os import path
from functools import lru_cache
from apsimNGpy.core.config import (
    set_apsim_bin_path,
    get_apsim_bin_path,
    auto_detect_apsim_bin_path,
)
from apsimNGpy.core.runner import get_apsim_version


app = typer.Typer(help="Manage APSIM binary path with flags like -u, -s, -v, -a")

@lru_cache()
def print_msg(msg: str, normal: bool = True):
    if normal:
        typer.echo(f"\033[96m{msg}\033[0m")
    else:
        typer.echo(f"\033[91m{msg}\033[0m")


@app.command()
def apsim_bin_path(
    update: str = typer.Option(None, "--update", "-u", help="Update APSIM bin path."),
    show: bool = typer.Option(False, "--show-bin-path", "-s", help="Show current bin path."),
    version: bool = typer.Option(False, "--version", "-v", help="Show APSIM version."),
    auto_search: bool = typer.Option(False, "--auto-search", "-a", help="Search for APSIM bin path."),
):
    """Unified command with shortcut flags like -u, -s, -v, -a."""

    if update:
        if not path.exists(update):
            print_msg(f"{update} does not exist", normal=False)
            raise typer.Exit(code=1)
        set_apsim_bin_path(update)
        print_msg(f"Updated APSIM bin path to: {update}")
        raise typer.Exit()

    if show:
        cbp = get_apsim_bin_path()
        print_msg(f"Current APSIM bin path: {cbp}")
        raise typer.Exit()

    if auto_search:
        auto = auto_detect_apsim_bin_path()
        if not auto:
            print_msg("No bin path detected", normal=False)
        else:
            print_msg(f"Detected APSIM bin path: {auto}")
        raise typer.Exit()

    if version:
        v = get_apsim_version()
        print_msg(f"APSIM Version: {v}")
        raise typer.Exit()

    # No options provided
    print_msg("No action provided. Use --help for options.", normal=False)
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
