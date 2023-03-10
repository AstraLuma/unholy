"""
Utilities for working with docker compose.
"""
from pathlib import Path
import subprocess


def find_compose() -> Path:
    """
    Walk up the parents, looking for a docker-compose file.

    Raises a FileNotFoundError if there isn't one.
    """
    curdir = Path.cwd().absolute()
    while curdir.parent != curdir:
        if (curdir / 'docker-compose.yml').exists():
            return curdir / 'docker-compose.yml'
        curdir = curdir.parent
    else:
        raise FileNotFoundError('Could not find a compose file')

# Annotations pulled from https://github.com/docker/compose/blob/7daa2a5325c2fe2608db90e6f4500fac21bd53b7/pkg/api/labels.go


def guess_annotations(compose: Path) -> dict:
    """
    Looks at a compose file and guesses the annotations its resources
    will have.
    """
    compose = compose.absolute()
    project_name = compose.parent.name
    return {
        'com.docker.compose.project': project_name,
        'com.docker.compose.project.working_dir': str(compose.parent),
        'com.docker.compose.project.config_files': str(compose),
    }


def nvim_annotations(compose: Path) -> dict:
    """
    Returns the annotations that should be used on the nvim container.
    """
    return guess_annotations(compose) | {
        'com.docker.compose.oneoff': "False",
    }


def nvim_name(compose: Path) -> str:
    """
    Returns the name that should be used for the nvim container.
    """
    annos = nvim_annotations(compose)
    base = annos['com.docker.compose.project']
    return f"{base}-nvim"


def ensure_up(compose: Path) -> None:
    """
    Ensures the given compose cluster is up.
    """
    subprocess.run(
        ['docker', 'compose', '--file', compose.absolute(), 'up', '--detach'],
        check=True, stdin=subprocess.DEVNULL,
    )
