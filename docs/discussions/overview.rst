============
Some Details
============

Ok, so what does Unholy actually do?


The Resources
=============

Throughout Unholy, we refer to several resources:

* **Workspace**: A Docker volume that's used to keep your git repo and other
  project materials, mounted as ``/workspace``.
* **Development Environment**: A Docker container where all commands are run. 
* **Unholyfiles**, **local config**, etc: The complete collection of data that
  Unholy uses to manage your project. (See :ref:`configuration`)
* **Unholy Project**: The entire collection of the above.

For example, ``unholy remake`` deletes and recreates the Development Environment
but doesn't touch your Workspace.


Development Environment Creation
================================

Unholy doesn't use Dockerfiles or create/cache images, or anything like that,
for a few reasons:

* It's expected that most of the time that you're recreating your development
  environment, it's because you changed an Unholyfile
* Config comes from many places, including a few user-specific ones, so caching
  would have to be user-specific, too
* The Dockerfile syntax is not particularly helpful in this use case

So Development Environment creation is like so:

1. Pull the base image (every time, no use building from a stale base)
2. Copy some data from the user, like git config and ssh known hosts
2. Run each Unholyfile's script

Forwarding and Piping
=====================

All connections in and out of the development environment are through Docker
exec and stdio forwarding. That's all.

Neovide is pointed to something like ``docker exec devenv nvim``.

SSH agent forwarding is two copies of socat chained together with Docker.

If you find this horrifying, first I'm sorry I inflicted this knowledge on you,
and second the name of the tool is Unholy.

Bootstrap
=========

Occasionally, when the development environment is unavailable, Unholy will spawn
a bootstrap container and use that for operations. It should be deleted
automatically when Unholy is done with it.
