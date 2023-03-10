from pathlib import Path

import click

from .compose import (
    find_compose, guess_annotations, nvim_annotations, nvim_name, ensure_up,
)
from .docker import find_networks, start_nvim
from .nvim import start_neovide

#: The container image to use for nvim
NVIM_CONTAINER = 'ghcr.io/astraluma/unholy:trunk'


@click.group()
def main():
    """
    An amalgamation of docker compose and neovim
    """


@main.command()
def workon():
    """
    Start neovim and open neovide
    """
    cpath = find_compose()
    print(f"{cpath=}")
    ensure_up(cpath)
    proj_annos = guess_annotations(cpath)
    print(f"{proj_annos=}")
    nv_annos = nvim_annotations(cpath)
    print(f"{nv_annos}")
    nv_name = nvim_name(cpath)
    print(f"{nv_name=}")
    nv = start_nvim(
        name=nv_name,
        image=NVIM_CONTAINER,
        labels=nv_annos,
        nets=list(find_networks(proj_annos)),
        src_dir=Path.cwd().absolute()
    )
    start_neovide(nv.port)


@main.command()
def shell():
    """
    Start a shell
    """
