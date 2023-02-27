import random


def pick_port() -> int:
    """
    Finds an open TCP port for neovide/nvim to use.
    """
    # TODO: Actually check if it's open.
    return random.randint(1024, 65535)
