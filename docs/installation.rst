=======================
Installation Guidelines
=======================

This is not going to give specific instructions, because I have not tested
Unholy on many machines yet.

Prerequisites
=============

First and formost, you need a Docker daemon somewhere.

Additionally, you need the following software installed locally:

* Git
* socat
* Docker CLI
* Neovide_.
* Python (3.10 or later)

Note that while you do not need a local Docker daemon running, your Docker
client must already be connected to the daemon and functional. (Unholy supports
`Docker Contexts`_ and it's suggested to use them for managing daemon connections.)

.. _Neovide: https://neovide.dev/
.. _Docker Contexts: https://docs.docker.com/engine/context/working-with-contexts/

Installing Unholy
=================

Unholy can be installed through Python. pipx_ is suggested.

With pipx, installation is:

.. code-block:: console

   $ pipx install unholy


.. _pipx: https://pypa.github.io/pipx/

Initial Configuration
=====================

Besides the aforementioned Docker client credentials, no initial configuration 
of Unholy is required.
