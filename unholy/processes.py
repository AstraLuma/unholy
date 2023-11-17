from .docker import container_run


def do_clone(container, config):
    container_run(
        container, ['git', 'clone', config['repository'], '/project'],
        check=True,
        encoding='UTF-8',
    )
