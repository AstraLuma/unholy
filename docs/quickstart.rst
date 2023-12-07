==========
Quickstart
==========

Ok, so you have Unholy, what do you do with it?

Make a Project
==============

An Unholy-native project will contain both an :ref:`Unholyfile <unholyfile>`
and a Compose_ file.

If we follow the `Try Docker Compose`_ guide, we'll end up with a compose file 
like this:

.. code-block:: yaml
   :caption: compose.yaml

   services:
     web:
       build: .
       ports:
         - "8000:5000"
     redis:
       image: "redis:alpine"

Additionally, the absolute minimum Unholyfile is this:

.. code-block::
   :caption: Unholyfile

You can actually skip creating an Unholyfile, and it'll
be equivalent.

.. _compose: https://docs.docker.com/compose/
.. _try docker compose: https://docs.docker.com/compose/gettingstarted/


Spawn your Environment
======================

With the basic files out of the way, you can ask unholy to create an environment:

.. code-block:: console

   $ unholy new --name demo git@github.com/YOU/YOURPROJECT.git

A lot of text will go by as Unholy creates the workspace, clones the repo, starts
compose services, and creates & configures your development environment.

This will create a vanilla Debian environment with pretty minimal utilities.
(Really, just enough for Unholy to work and a few utilities for humans.)


Access Your Environment
=======================

Ok, so you've got this shiny development environment sitting on a computer
somewhere. It doesn't do you any good if you can't access it.

In order to open Neovide and a shell, use these:

.. code-block:: console

   $ unholy neovide demo
   $ unholy shell demo
   root@demo:/workspace# 

These two commands do related things:

* ``unholy neovide`` opens Neovide and connects it to neovim running in the
  development environment
* ``unholy shell`` drops you into bash inside the development environment


Customizing You Environment
===========================

Ok, so one of the cool things about containers is recreatable artifacts and
environments, and Unholy is no exception.

In summary, the Unholyfile is a script with some TOML_ headmatter. The framework
would look something like:

.. code-block::
   :caption: Unholyfile
   :linenos:

   ---
   ---
   #!/bin/sh
   set -e


.. _toml: https://toml.io/

Pick an Image
-------------

Since this is a Python project, let's start with a Python environment.

.. code-block::
   :caption: Unholyfile
   :linenos:
   :emphasize-lines: 2-3

   ---
   [dev]
   image = "python:3"
   ---
   #!/bin/sh
   set -e

.. note::

   The container image must be Debian-based.

Add Some Dependencies
---------------------

Most projects have some dependencies that need to happen: test runners, git
tooling, etc. Let's install them.

.. code-block::
   :caption: Unholyfile
   :linenos:
   :emphasize-lines: 7-8

   ---
   [dev]
   image = "python:3"
   ---
   #!/bin/sh
   set -e
   pip install -r requirements.txt
   pip install pytest

.. note::

   Since this is a dedicated, single-purpose environment, you do not need to use
   a Python virtual environment or similar.


Recreate the Environment
========================

Since we've changed the Unholyfile (in particular, we've changed the base image),
we need to recreate the environment:

.. code-block:: console

   $ unholy remake demo

This will recreate the development environment without touching your workspace
files. Note that any open shell or Neovim sessions will be uncerimoniously
closed, so make sure that your work is saved.
