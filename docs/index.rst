===========================
And thus I shall call it...
===========================

Cooperates with Docker Compose, injects an nvim-based container
into it, and connects neovide to it.

You can call it what you'd like, but I'm going to call this union Unholy.

What?
=====

Unholy is a tool to create and manage Docker-based development
environments--it's a dev container implementation.

Unholy performs all operations over the Docker CLI; no side-band channels or open
ports are used. Both local and remote daemons are supported.

* Uses Neovim and Neovide as the editing UI
* Connects the development environment to its Docker daemon, so container and
  compose operations work
* Your SSH agent is forwarded, so SSH operations (including Git-based ones) work
* Your Git config and some SSH data is copied (notably not your private keys;
  you should use an ssh agent for that)
* Multiple daemons are supported through Docker Contexts

Contents
========

.. toctree::
   :titlesonly:

   installation
   quickstart
   cookbook/index
   discussions/index
   reference/index



Indices and tables
==================

* :ref:`genindex`
