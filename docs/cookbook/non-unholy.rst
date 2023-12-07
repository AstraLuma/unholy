======================================================
How To Use Unholy With a Project Without an Unholyfile
======================================================

For reasons, you will probably need to use Unholy with a project that doesn't
have an Unholy file.

Create Your Unholy Project
==========================

As per normal, call ``unholy new`` with your repo:

.. code-block:: console
   
   $ unholy new git@git.host/you/repo.git

In the output, you might be able to spot a line:

   Unholyfile not found in project. Continuing with defaults

Edit Your Unholyfile
====================

As discussed in :ref:`configuration`, some data is kept locally on your
workstation. You can make your Unholyfile adjustments in there instead
in the workspace.

This file is typically ``~/.config/unholy/PROJECT.Unholyfile``.

You can put all settings and scripting in there just like an Unholyfile
in the workspace.

Recreate Your Environment
=========================

As mentioned in the quickstart, you'll probably want to do this every time
you edit your Unholyfile.

.. code-block:: console

   $ unholy remake PROJECT
