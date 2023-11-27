import functools
from pathlib import Path
import subprocess
import sys

import click

from .compose import (
    UnholyCompose,
    find_compose, guess_annotations, nvim_annotations, nvim_name, ensure_up,
)
from .config import edit_config, get_config_stack, get_script_stack, project_config_path
from .docker import find_networks, start_nvim
from .git import guess_project_from_url, pull_file
from .nvim import start_neovide
from .processes import do_clone, run_compose


#: The container image to use for nvim
NVIM_CONTAINER = 'ghcr.io/astraluma/unholy:trunk'


def format_exceptions(func):
    """
    Nicely format exceptions for end users
    """
    @functools.wraps(func)
    def _(*pargs, **kwargs):
        try:
            return func(*pargs, **kwargs)
        except subprocess.CalledProcessError as exc:
            if exc.stderr is not None:
                sys.stderr.write(exc.stderr)
            elif exc.stdout is not None:
                sys.stderr.write(exc.stdout)
            print(f"Call to `{' '.join(exc.cmd)}` failed", file=sys.stderr)
            sys.exit(exc.returncode)
    return _


@click.group()
def main():
    """
    An amalgamation of docker compose and neovim
    """


@main.command()
@click.option('--name', help="Project name (default: guess from repository URL)")
@click.argument('repository')
@click.option('--remote', '-o', help="Name of the remote (default: origin)")
@click.option('--branch', '-b', help="Namoe of the branch (default: remote's HEAD)")
@format_exceptions
def clone(name, repository, remote, branch):
    """
    Create a new project from a git repo
    """
    name = name or guess_project_from_url(repository)
    if project_config_path(name).exists():
        click.confirm(
            "This project exists locally. Are you sure you want to overwrite it?",
            abort=True,
        )
    uf = pull_file(repository, 'Unholyfile', branch=branch)

    # Write out the project information
    with edit_config(project_config_path(name)) as project:
        project['repository'] = repository
        # TODO: Write out environment

    config = get_config_stack(project_name=name, project_config=uf)

    # Do initialization
    composer = UnholyCompose(name, config)
    if (c := composer.devenv_get()) is not None:
        c.remove(force=True)

    if composer.workspace_get() is not None:
        click.confirm(
            "Project volume already exists. Are you sure you want to blow it away?",
            abort=True,
        )
        composer.project_volume_delete()
    composer.project_volume_create()

    with composer.bootstrap_spawn() as container:
        do_clone(container, config)
        run_compose(container, config, ['up', '--detach'])

    composer.devenv_create(
        get_script_stack(project_name=name, project_config=uf),
    )


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
