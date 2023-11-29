import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import click
import docker
import docker.errors
import docker.models.images
import docker.types
from docker.transport.unixconn import UnixHTTPAdapter
import docker.utils


def get_client(use: str | None = None) -> docker.DockerClient:
    """
    Get a docker client for the given docker context
    """
    context = docker.ContextAPI.get_context(use)
    return docker.DockerClient(
        base_url=context.endpoints["docker"]["Host"],
        tls=context.TLSConfig
    )


def socket_path(client) -> None | Path:
    """
    Returns the docker socket path, if available.
    """
    adapter = client.api._custom_adapter
    # passed scheme | stored_scheme | adapter
    # ---------------------------------------
    # http+unix     | http+docker   | UnixHTTPAdapter
    # npipe         | http+docker   | NpipeHTTPAdapter
    # ssh           | http+docker   | SSHHTTPAdapter
    if isinstance(adapter, UnixHTTPAdapter):
        return adapter.socket_path


def smart_pull(client, image) -> docker.models.images.Image:
    """
    Pulls the given image with click progress.
    """
    repository, image_tag = docker.utils.parse_repository_tag(image)
    tag = image_tag or 'latest'

    with click.progressbar(
        client.api.pull(repository, tag=tag, stream=True, decode=True),
        label='Pulling',
        item_show_func=lambda item: (
            item.get('status', None) if isinstance(item, dict) else str(item)
        ),
    ) as bar:
        for line in bar:
            # print(f"{line=}")
            if 'progressDetail' not in line:
                continue
            if 'total' in line['progressDetail']:
                bar.length = line['progressDetail']['total']
            if 'current' in line['progressDetail']:
                bar.update(line['progressDetail']['current'], line)

    return client.images.get(f"{repository}{'@' if tag.startswith('sha256:') else ':'}{tag}")


def mount(mountpoint: str, volume: docker.models.volumes.Volume, **opts) -> docker.types.Mount:
    return docker.types.Mount(
        target=mountpoint,
        source=volume.name,
        type='volume',
        **opts
    )


class DockerExec:
    @classmethod
    def create(cls, container, /, **opts):
        """
        Create an exec.

        See :meth:`docker.api.exec_api.ExecApiMixin.exec_create`
        """
        resp = container.client.api.exec_create(
            container.id, **opts,
        )
        return cls(container.client, resp['Id'])

    def __init__(self, client, id):
        self.api = client.api
        self.id = id

    def inspect(self) -> dict:
        """
        Get some basic info.

        See https://docs.docker.com/engine/api/v1.43/#tag/Exec/operation/ExecInspect
        """
        return self.api.exec_inspect(self.id)

    def resize(self, height=None, width=None):
        """
        Resize the PTY of the command.
        """
        self.api.exec_resize(self.id, height=height, width=width)

    def start(self, **opts):
        """
        Start the command. You're kinda on your own.

        See :meth:`docker.api.exec_api.ExecApiMixin.exec_start`
        """
        return self.api.exec_start(self.id, **opts)

    def start_with_pipes(self, *, stdin=None, stdout=None, stderr=None, tty=False):
        """
        Start the command, but handle passing data between everything.
        """
        sock = self.start(
            detach=False, tty=tty, stream=False, socket=True, demux=False,
        )
        # I think stdin is just the raw stream?
        sock  # Make flake8 happy

        raise NotImplementedError

    # TODO: Look into sending signals


def container_run(
    container, cmd, *,
    stdout=None, stderr=None,
    check: bool = False,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    encoding: str | None = None,
    errors: str = 'strict',
    tty=False,
) -> subprocess.CompletedProcess:
    """
    Presents a subprocess-like interface to container processes.
    """
    if stdout is None:
        sys.stdout.flush()
        pipe_out = sys.stdout.buffer
    elif stdout is subprocess.DEVNULL:
        pipe_out = open(os.devnull, 'wb')
    elif stdout is subprocess.PIPE:
        pipe_out = io.BytesIO()
    else:
        pipe_out = stdout
        # FIXME: Handle if we're handed a text-mode pipe

    if stderr is None:
        sys.stderr.flush()
        pipe_err = sys.stderr.buffer
    elif stderr is subprocess.DEVNULL:
        pipe_err = open(os.devnull, 'wb')
    elif stderr is subprocess.PIPE:
        pipe_err = io.BytesIO()
    elif stderr is subprocess.STDOUT:
        pipe_err = pipe_out
    else:
        pipe_err = stderr
        # FIXME: Handle if we're handed a text-mode pipe

    exec = DockerExec.create(
        container, cmd=cmd,
        stdout=True, stderr=True,
        # stdin=stdin,  privileged=privileged, user=user,
        environment=env, workdir=cwd, tty=tty,
    )
    sock = exec.start(
        detach=False, tty=False, stream=False, socket=True,
        demux=False,
    )

    pipemap = {
        docker.utils.socket.STDOUT: pipe_out,
        docker.utils.socket.STDERR: pipe_err,
    }

    for pipe, chunk in docker.utils.socket.frames_iter(sock, False):
        pipemap[pipe].write(chunk)

    info = exec.inspect()

    assert not info['Running']
    retcode = info['ExitCode']
    outval = pipe_out.getvalue() if isinstance(pipe_out, io.BytesIO) else None
    errval = pipe_err.getvalue() if isinstance(pipe_err, io.BytesIO) else None
    if encoding:
        if outval is not None:
            outval = outval.decode(encoding, errors)
        if errval is not None:
            errval = errval.decode(encoding, errors)
    if check and retcode:
        raise subprocess.CalledProcessError(
            retcode, cmd,
            output=outval, stderr=errval)
    else:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=info['ExitCode'],
            stdout=outval,
            stderr=errval,
        )


def inject_and_run(
    container: docker.models.containers.Container,
    script: str,
    name: str = 'injected-script',
    **opts
):
    """
    Loat the given script into the container, and then run it with
    :func:`container_run`.
    """
    # Note: Cannot inject files into the tmpfs
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:') as tf:
        ti = tarfile.TarInfo(name)
        bscript = script.encode('utf-8')
        ti.size = len(bscript)
        ti.mode = 0o755
        tf.addfile(ti, fileobj=io.BytesIO(bscript))
    buffer.seek(0)
    container.put_archive('/', buffer)

    try:
        container_run(
            container, [f'/{name}'],
            check=True, tty=True,
        )
    finally:
        container_run(
            container, ['rm', '-rf', f'/{name}'],
            check=True,
        )
