from .docker import container_run


def do_clone(container, config):
    container_run(
        container, ['git', 'clone', config['repository'], '/project'],
        # FIXME: Handle stdin for passwords and such
        check=True,
    )


def compose_cmd(config) -> list[str]:
    """
    Produce the compose base command based on the config.
    """
    return [
        'docker', 'compose',
        '--file', config['compose']['file'],
        '--project-name', config['compose']['project'],
        '--project-directory', '/project',
    ]


def run_compose(container, config, cmd: list[str]):
    return container_run(
        container, [*compose_cmd(config), *cmd],
        check=True, cwd='/project',
    )
