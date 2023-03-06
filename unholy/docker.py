from dataclasses import dataclass
from pathlib import Path
import signal
import urllib.parse

import docker
from docker.transport.unixconn import UnixHTTPAdapter
from unholy.nvim import pick_port


print("Creating docker client")
client = docker.from_env()


def socket_path() -> None | Path:
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


def find_networks(annos: dict):
    """
    Searches the docker networks for any that match any of the annotations.
    """
    for net in client.networks.list():
        labels = net.attrs['Labels']
        if any(labels.get(k, None) == v for k, v in annos.items()):
            yield net


@dataclass
class StartedNvim:
    port: int


def start_nvim(
    name: str,
    image: str,
    labels: dict,
    nets: list,
    src_dir: Path | None = None,
    socket_path: Path | None = None,
) -> StartedNvim:
    """
    Start the nvim container.

    Args:
    * name: The container name
    * image: The container image to use
    * port: The network port to listen on
    * labels: Labels to use
    * nets: List of networks to connect
    * src_dir: The project directory to mount within
    * docker_socket: The socket path for docker
    """
    # TODO: re-use existing containers
    try:
        oldc = client.containers.get(name)
    except docker.errors.NotFound:
        pass
    else:
        print("Killing old container...")
        oldc.stop()
        try:
            # Will probably error because auto_remove
            oldc.remove()
        except (docker.errors.NotFound, docker.errors.APIError):
            pass
    port = pick_port()
    print(f"{port=}")
    print("Pulling...")
    img = client.images.pull(image)
    print(f"{img.tags=}")
    mounts = []
    if src_dir:
        mounts.append(docker.types.Mount(
            target='/project',
            source=str(src_dir),
            type='bind',
        ))
    print(f"{mounts=}")
    assert nets
    first_net, *rest_nets = nets
    c = client.containers.create(
        image=img.tags[0] if img.tags else img.id,  # Using the tag is nicer for docker ps/etc
        command=['nvim', '--headless', '--listen', f'0.0.0.0:{port}'],
        auto_remove=True,  # FIXME: Attempt to re-use instead
        detach=True,
        # environment=[],
        init=True,
        labels=labels,
        mounts=mounts,
        name=name,
        network=first_net.name,
        ports={
            f"{port}/tcp": ('127.0.0.1', port),
        },
        # TODO: Don't run as root
        working_dir='/project',
    )
    print(f"{c=}")
    for net in rest_nets:
        net.connect(c)

    print("Starting...")
    c.start()

    return StartedNvim(
        port=port,
    )
