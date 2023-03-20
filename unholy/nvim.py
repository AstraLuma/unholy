import random
import subprocess


def pick_port() -> int:
    """
    Finds an open TCP port for neovide/nvim to use.
    """
    # TODO: Actually check if it's open.
    return random.randint(1024, 65535)


def start_neovide(port: int):
    """
    Open Neovide, pointed at the neovim instanse at the given port.
    """
    # Neovide detaches by default
    subprocess.run(
        ['neovide', '--remote-tcp', f"127.0.0.1:{port}"],
        stdin=subprocess.DEVNULL, check=True,
    )
