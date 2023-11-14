from pathlib import Path

import click

from .config import parse
from .git import pull_file
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
@click.argument('repository')
@click.option('--remote', '-o', help="Name of the remote (default: origin)")
@click.option('--branch', '-b', help="Namoe of the branch (default: remote's HEAD)")
def clone(repository, remote, branch):
    """
    Create a new project from a git repo
    """
    uf = pull_file(repository, 'Unholyfile', branch=branch)
    config, project_script = parse(uf)


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
