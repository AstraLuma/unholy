.. _unholyfile:

==============
The Unholyfile
==============

The only configuration used by Unholy is The Unholyfile, so let's discuss it.

Format
======

.. code-block::
   :caption: Unholyfile

   ---
   # This is headmatter. It is TOML.
   key = "value"
   
   [section]
   key = "value"
   ---
   #!/usr/bin/sh
   # This is the script

An Unholyfile is a script with TOML_ headmatter.

Both the script and the headmatter are optional.

Delimiters are lines with nothing but dashes, and at least 3 of them.

If there is headmatter, it must be preceeded by a delimiter. That delimiter
must by on the first line.

If there is both headmatter and a script, they must be separated by a
delimiter. If there is headmatter but no script, the trailing delimiter is
optional.

An empty file is valid. A file with no delimiters is interpreted as all script
with no headmatter.

A script may start with a shbang (``#!``). If it does, it must be on the line
immediately following the delimiter (if present).

.. _toml: https://toml.io/

Schema
======

As documentation and information, here is the base Unholyfile (see
:ref:`configuration`) included in Unholy:

.. note::

   TOML does not have a null/nil/None/etc, it only has missing keys. Commented 
   out lines are values that default to null (aka missing).

.. literalinclude:: /../unholy/core.Unholyfile
