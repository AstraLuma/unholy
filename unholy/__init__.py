from collections.abc import Mapping
from dataclasses import dataclass
import functools
import subprocess
import sys
import time

import click

from .compose import (
    UnholyCompose,
)
from .config import edit_config, get_config_stack, get_script_stack, project_config_path
from .git import guess_project_from_url, pull_file
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
# @click.option('--remote', '-o', help="Name of the remote (default: origin)")
@click.option('--branch', '-b', help="Namoe of the branch (default: remote's HEAD)")
@format_exceptions
def new(name, repository, branch):
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
        composer.workspace_delete()
    composer.workspace_create()

    with composer.bootstrap_spawn() as container:
        do_clone(container, config)
        run_compose(container, config, ['up', '--detach'])

    composer.devenv_create(
        get_script_stack(project_name=name, project_config=uf),
    )


@dataclass
class UnholyBits:
    #: Unholyfile contents from the project
    unholyfile: str
    #: Config stack
    config: Mapping
    #: Compose for invoking docker
    compose: UnholyCompose


def get_bits(name: str) -> UnholyBits:
    """
    Does the right invocations to produce a configured compose.
    """
    # Start with mostly-complete versions of these objects.
    config = get_config_stack(project_name=name)
    composer = UnholyCompose(name, config)
    uf = composer.get_unholyfile()

    # Recreate these with more complete info
    config = get_config_stack(project_name=name, project_config=uf)
    composer = UnholyCompose(name, config)
    return UnholyBits(
        unholyfile=uf,
        config=config,
        compose=composer,
    )


@main.command()
@click.argument('name')
@format_exceptions
def remake(name):
    """
    Recreate the devenv.
    """
    unholy = get_bits(name)
    # Do initialization
    if (c := unholy.compose.devenv_get()) is not None:
        c.remove(force=True)

    with unholy.compose.bootstrap_spawn() as container:
        run_compose(container, unholy.config, ['up', '--detach'])

    unholy.compose.devenv_create(
        get_script_stack(project_name=name, project_config=unholy.unholyfile),
    )


@main.command()
@click.argument('name')
@format_exceptions
def neovide(name):
    """
    Open neovim/neovide inside the devenv
    """
    unholy = get_bits(name)
    devenv = unholy.compose.devenv_get()
    with unholy.compose.docker_script(
        'exec',
        '--interactive',
        '--workdir', unholy.compose.PROJECT_MOUNTPOINT,
        devenv,
        'nvim',
    ) as scriptfile:
        subprocess.run(['neovide', '--neovim-bin', scriptfile,], check=True)
        time.sleep(1)  # Magic wait so neovide has time to exec the script


@main.command()
@click.argument('name')
@format_exceptions
def shell(name):
    """
    Open a shell inside the devenv
    """
    unholy = get_bits(name)
    devenv = unholy.compose.devenv_get()
    cmd = unholy.compose.docker_cmd(
        'exec',
        '--interactive', '--tty',
        '--workdir', unholy.compose.PROJECT_MOUNTPOINT,
        devenv,
        '/bin/bash',  # TODO: Read shell from config
    )
    subprocess.run(cmd, check=True)
