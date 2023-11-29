"""
Utilities for working with docker compose.
"""
from contextlib import contextmanager, ExitStack
import enum
import io
import os.path
import shlex
import tarfile
import tempfile
from typing import Iterable, Iterator

import docker
import docker.errors
import docker.models

from .docker import get_client, smart_pull, mount, inject_and_run


class Label(enum.StrEnum):
    # From https://github.com/docker/compose/blob/7daa2a5325c2fe2608db90e6f4500fac21bd53b7/pkg/api/labels.go#L28-L59
    #: allow to track resource related to a compose project
    Project = "com.docker.compose.project"
    #: allow to track resource related to a compose service
    Service = "com.docker.compose.service"
    #: stores configuration hash for a compose service
    ConfigHash = "com.docker.compose.config-hash"
    #: stores the container index of a replicated service
    ContainerNumber = "com.docker.compose.container-number"
    #: allow to track resource related to a compose volume
    Volume = "com.docker.compose.volume"
    #: allow to track resource related to a compose network
    Network = "com.docker.compose.network"
    #: stores absolute path to compose project working directory
    WorkingDir = "com.docker.compose.project.working_dir"
    #: stores absolute path to compose project configuration files
    ConfigFiles = "com.docker.compose.project.config_files"
    #: stores absolute path to compose project env file set by `- -env-file`
    EnvironmentFile = "com.docker.compose.project.environment_file"
    #: stores value 'True' for one-off containers created by `compose run`
    OneOff = "com.docker.compose.oneoff"
    #: stores unique slug used for one-off container identity
    Slug = "com.docker.compose.slug"
    #: stores digest of the container image used to run service
    ImageDigest = "com.docker.compose.image"
    #: stores service dependencies
    Dependencies = "com.docker.compose.depends_on"
    #: stores the compose tool version used to build/run application
    Version = "com.docker.compose.version"
    #: stores the builder(classic or BuildKit) used to produce the image.
    ImageBuilder = "com.docker.compose.image.builder"
    #: is set when container is created to replace another container(recreated)
    ContainerReplace = "com.docker.compose.replace"


class Compose:
    """
    Wrapper around a docker client that does all the extra compose bits.

    (Mostly labelling.)
    """

    def __init__(self, name, unholy_config):
        self.config = unholy_config
        self.project_name = \
            unholy_config.get('compose', {}).get('project') \
            or name

        self.client = get_client()

    def volume_list(self) -> Iterator[docker.models.volumes.Volume]:
        """
        Enumerate realized volumes associated with this project.
        """
        for vol in self.client.volumes.list():
            if vol.attrs['Labels'].get(Label.Project) == self.project_name:
                yield vol

    def volume_create(self, name, *, labels=None) -> docker.models.volumes.Volume:
        """
        Create a volume in the compose project
        """
        labels = labels or {}
        return self.client.volumes.create(
            name=f"{self.project_name}_{name}",
            labels={
                Label.Project: self.project_name,
                Label.Volume: name,
            } | labels,
        )

    def _socket_mount_opts(self):
        """
        Get the options needed for a container to access the docker socket.
        """
        # TODO: Use https://github.com/Tecnativa/docker-socket-proxy instead?
        return {
            'environment': {
                'DOCKER_HOST': 'unix:///var/run/docker.sock',
            },
            'mounts': [
                docker.types.Mount(
                    target='/var/run/docker.sock',
                    source='/var/run/docker.sock',  # FIXME: Detect this
                    type='bind',
                )
            ],
            # 'privledged': True,
        }

    def container_list(self) -> Iterator[docker.models.containers.Container]:
        """
        Enumerate realized containers associated with this project.
        """
        for con in self.client.containers.list(all=True):
            if con.labels.get(Label.Project) == self.project_name:
                yield con

    def container_create(
        self, service, image, *,
        one_off=None, labels=None, mount_docker_socket=False,
        environment=None, mounts=None,
        **opts
    ):
        # FIXME: Implement service increment
        default_labels = {
            Label.Project: self.project_name,
            Label.Service: service,
        }
        if one_off is not None:
            default_labels[Label.OneOff] = repr(bool(one_off))
        if labels is not None:
            labels = default_labels | labels
        else:
            labels = default_labels
        if mount_docker_socket:
            socket_bits = self._socket_mount_opts()
            if environment is None:
                environment = {}
            environment |= socket_bits.pop('environment', {})
            if mounts is None:
                mounts = []
            mounts += socket_bits.pop('mounts', [])
            opts |= socket_bits

        return self.client.containers.create(
            name=f"{self.project_name}-{service}-1",
            image=image,
            labels=labels,
            environment=environment,
            mounts=mounts,
            **opts
        )


class UnholyCompose(Compose):
    """
    Adds unholy-specific resource concepts to Compose.
    """

    # There's three resources that unholy cares about:
    # * The workspace--the persistent place to keep the project
    # * The devenv--A semi-ephemeral container the user actually works in
    # * Bootstrap container--Ephemeral container used for some operations when
    #   a devenv might not be available

    BOOTSTRAP_IMAGE = 'ghcr.io/astraluma/unholy/bootstrap:nightly'
    PROJECT_MOUNTPOINT = '/project'
    DEVENV_SERVICE = 'devenv'

    def __init__(self, *p, **kw):
        super().__init__(*p, **kw)
        self.project_volume_name = self.config.get('dev', {}).get('volume')

    def workspace_get(self) -> None | docker.models.volumes.Volume:
        """
        Searches for the project volume, or returns None
        """
        for vol in self.volume_list():
            if vol.attrs['Labels'].get(Label.Volume) == self.project_volume_name:
                return vol

    def workspace_create(self) -> docker.models.volumes.Volume:
        """
        Creates a fresh project volume
        """
        assert self.workspace_get() is None
        return self.volume_create(self.project_volume_name)

    def workspace_delete(self):
        """
        Deletes the project volume
        """
        vol = self.workspace_get()
        if vol is not None:
            vol.remove()

    @contextmanager
    def bootstrap_spawn(self) -> docker.models.containers.Container:
        """
        Start a bootstrap container and clean it up when done.
        """
        img = smart_pull(self.client, self.BOOTSTRAP_IMAGE)
        proj = self.workspace_get()
        assert proj is not None
        cont = self.container_create(
            'bootstrap', img,
            one_off=True,
            init=True,
            auto_remove=True,
            mounts=[
                mount(self.PROJECT_MOUNTPOINT, proj),
            ],
            working_dir=self.PROJECT_MOUNTPOINT,
            mount_docker_socket=True,
            # TODO: ssh agent forward
        )
        cont.start()
        try:
            yield cont
        finally:
            cont.stop()
            try:
                cont.remove()
            except docker.errors.APIError:
                # This usually happens, because auto_remove
                pass

    def devenv_get(self) -> None | docker.models.containers.Container:
        """
        Get the devenv container, if it exists.
        """
        for con in self.container_list():
            if con.labels.get(Label.Service) == self.DEVENV_SERVICE:
                return con

    def devenv_create(self, scripts: Iterable[str]):
        """
        Create the devenv container.

        Args:
            scripts: The list of configuration scripts to run.
        """
        img = smart_pull(self.client, self.config['dev']['image'])
        proj = self.workspace_get()
        assert proj is not None
        cont = self.container_create(
            self.DEVENV_SERVICE, img,
            command=['sleep', 'infinity'],
            init=True,
            mounts=[
                mount(self.PROJECT_MOUNTPOINT, proj),
                # TODO: Other mounts
            ],
            tmpfs={
                '/tmp': '',
            },
            working_dir=self.PROJECT_MOUNTPOINT,
            mount_docker_socket=True,
            # TODO: ssh agent forward
            # TODO: Networks
        )
        cont.start()
        for i, script in enumerate(scripts):
            if script:
                inject_and_run(
                    cont, fix_script(script),
                    cwd='/project',
                    name=f'unholyscript-{i}'
                )
        return cont

    def get_unholyfile(self) -> str:
        """
        Gets the config file from the workspace.
        """
        with ExitStack() as stack:
            if (cont := self.devenv_get()) is not None:
                pass
            else:
                cont = stack.enter_context(self.bootstrap_spawn())

            tarblob, _ = cont.get_archive(f'{self.PROJECT_MOUNTPOINT}/Unholyfile')
            buffer = io.BytesIO()
            for bit in tarblob:
                buffer.write(bit)
            buffer.seek(0)
            with tarfile.open(fileobj=buffer, mode='r|') as tf:
                for member in tf:
                    name = os.path.basename(member.name)
                    if name == 'Unholyfile':
                        assert member.isfile()
                        return tf.extractfile(member).read().decode('utf-8')

        raise RuntimeError("Unable to find Unholyfile in workspace.")

    def docker_cmd(self, *cmd: str | docker.models.containers.Container):
        """
        Builds the command to invoke docker.
        """
        prefix = ['docker']
        # TODO: Docker contexts
        return [*prefix, *(
            bit.name if isinstance(bit, docker.models.containers.Container)
            else str(bit)
            for bit in cmd
        )]

    @contextmanager
    def docker_script(self, *cmd: str | docker.models.containers.Container, **opts):
        """
        Writes out a script to invoke docker itself.
        """
        with tempfile.NamedTemporaryFile('wt+', delete_on_close=False, **opts) as ntf:
            ntf.write("#!/bin/bash\n")  # We use a bashism below
            ntf.write('exec ')
            ntf.write(shlex.join(self.docker_cmd(*cmd)))
            ntf.write(' "$@"\n')
            ntf.flush()

            os.chmod(ntf.name, 0o755)

            # Gotta close the file, else "text file busy"
            ntf.close()
            yield ntf.name


def fix_script(script: str) -> str:
    if not script.startswith('#!'):
        script = '#!/bin/sh\n' + script
    return script
