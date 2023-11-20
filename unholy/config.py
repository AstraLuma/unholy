"""
Handle Unholyfile parsing
"""
import collections
from collections.abc import Mapping, MutableMapping
import contextlib
import functools
import importlib.resources
import io
import os
import pathlib
import re
from typing import Iterable, Iterator

import appdirs
import tomlkit


def parse(text) -> tuple[MutableMapping, str]:
    """
    Given a text blob, pull out the head matter and parse it.
    """
    _, head, _, tail = _split_headmatter(text)
    head = tomlkit.parse(head)
    return head, tail


_DIVIDER = re.compile('^-{3,}$')


def _split_headmatter(text):
    if not text:
        # Special handling for empty files
        yield ""  # ---
        yield ""  # head
        yield ""  # ---
        yield ""  # tail
        return
    head = ""
    tail = ""
    fobj = io.StringIO(text)
    first = next(fobj)
    if _DIVIDER.match(first.strip()):
        yield first
        # We have headmatter
        for line in fobj:
            if _DIVIDER.match(line.strip()):
                yield head
                yield line
                break
            else:
                head += line
        else:
            # No trailing ---
            yield head
            yield ""  # ---
            yield ""  # tail
    else:
        # No leading ---
        yield ""  # ---
        yield ""  # head
        yield ""  # ---
        tail = first

    tail += fobj.read()
    yield tail


@contextlib.contextmanager
def edit_config(path: str | os.PathLike, *, create: bool = True) -> Iterator[tomlkit.TOMLDocument]:
    """
    Edit a config file in-place while preserving formatting.

    Context manager that yields a dict-like (technically,
    tomlkit.TOMLDocument).
    """
    try:
        f = open(path, 'r+t', encoding='utf-8')
    except FileNotFoundError:
        if create:
            f = open(path, 'w+t', encoding='utf-8')
        else:
            raise
    with f:
        f.seek(0)
        leader, head, divider, tail = _split_headmatter(f.read())

        doc = tomlkit.parse(head)
        yield doc

        f.seek(0)
        # FIXME: Have intelligence about dividers and prefer to omit if
        # original omitted?
        f.write(leader or '---\n')
        f.write(tomlkit.dumps(doc))
        f.write(divider or '---\n')
        f.write(tail)
        f.truncate()


@functools.cache
def app_dirs() -> appdirs.AppDirs:
    """
    AppDirs instance
    """
    return appdirs.AppDirs("unholy")


@functools.cache
def config_path() -> pathlib.Path:
    """
    site_config_dir but Path
    """
    path = pathlib.Path(app_dirs().user_config_dir)
    if not path.exists():
        path.mkdir(parents=True)
    return path


def project_config_path(name: str) -> pathlib.Path:
    """
    Get the path for local project config
    """
    return config_path() / f"{name}.Unholyfile"


class ConfigStack(collections.ChainMap):
    def __getitem__(self, key):
        value = super().__getitem__(key)
        if isinstance(value, dict):
            return type(self)(*(
                inner[key]
                for inner in self.maps
                if key in inner
            ))
        else:
            return value


def _get_file_stack(*, project_name=None, project_config=None) -> Iterable[tuple[MutableMapping, str]]:
    """
    Get the complete Unholyfile stack

    Starts at the back (core) and works forward (project)
    """
    # Unholy core
    yield parse(
        importlib.resources.files('unholy')
        .joinpath('core.Unholyfile').open('r', encoding='utf-8').read()
    )

    # User config
    conf = config_path() / 'Unholyfile'
    if conf.exists():
        yield parse(conf.read_text(encoding='utf-8'))

    # Project config
    if project_name:
        conf = project_config_path(project_name)
        if conf.exists():
            yield parse(conf.read_text(encoding='utf-8'))

    # Repo file
    if project_config and isinstance(project_config, str):
        yield parse(project_config)


def get_config_stack(*, project_name=None, project_config=None) -> Mapping:
    """
    Get the complete configuration stack up for a given project.

    Also applies defaults.
    """
    defaults = {
        'compose': {'project': project_name} if project_name else {}
    }

    stack = [
        defaults,
        # Standard stack
        *(
            config
            for config, _ in _get_file_stack(
                project_name=project_name,
                project_config=project_config,
            )
        ),
    ]
    if project_config and not isinstance(project_config, str):
        stack += [project_config]

    return ConfigStack(*reversed(stack))


def get_script_stack(*, project_name=None, project_config=None) -> Iterable[str]:
    """
    Get the complete configuration script stack.
    """
    return [
        script
        for _, script in _get_file_stack(
            project_name=project_name,
            project_config=project_config,
        )
    ]
