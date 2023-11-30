from .docker import container_run


def do_clone(container, directory, config, *, branch=None, remote=None):
    opts = []
    if remote:
        opts += ['--origin', remote]
    if branch:
        opts += ['--branch', branch]

    container_run(
        container, ['git', 'clone', *opts, config['repository'], directory],
        # FIXME: Handle stdin for passwords and such
        check=True,
    )
