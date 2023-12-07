====
How To Share a Workspace with Compose
====
When using Docker Compose, it's very common to share your project with the
service containers through a bind mount, such as:

.. code-block:: yaml
   :caption: compose.yaml
   :linenos:
   :emphasize-lines: 6-7
   
   services:
     web:
       build: .
       ports:
         - "8000:5000"
       volumes:
         - .:/code
     redis:
       image: "redis:alpine"


However, this tries to bind a directory from the docker daemon host, not
inside the development environment. So how does one share code with services?

Explicitly Name Your Workspace
==============================

While this isn't strictly necessary, since you're going to refer to your
workspace volume by name, I suggest explicitly naming it.

.. code-block::
   :caption: Unholyfile
   :linenos:
   :emphasize-lines: 4

   ---
   [dev]
   # ...
   volume = "workspace"
   # ...
   ---
   # ...

.. warning::

   If anyone has an Unholy workspace, and you change this value from
   ``"workspace"``, everyone must recreate their entire Unholy project.
   ``unholy remake`` will not save you.

Tell Compose
============

Ok, the actually important part:

1. Tell Compose about your workspace volume
2. Mount it into your services

Like so:

.. code-block:: yaml
   :caption: compose.yaml
   :linenos:
   :emphasize-lines: 7, 11-12
   
   services:
     web:
       build: .
       ports:
         - "8000:5000"
       volumes:
         - workspace:/code
     redis:
       image: "redis:alpine"

   volumes:
     workspace:

.. warning::

   ``docker compose down --volumes`` will now attempt to delete your workspace.
   It'll fail (probably), but it's going to try.

Recreate Your Services
======================

Ask Compose to recreate your services:

.. code-block:: console

   $ docker compose up -d


All Done!
=========

Now things like code auto-reload should work as expected.
