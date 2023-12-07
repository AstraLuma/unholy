.. _configuration:

=============
Configuration
=============

When Unholy creates or manipulates projects, it uses :ref:`Unholyfiles <unholyfile>`
from several sources (in order from back to front in the stack):

1. ``core.Unholyfile`` from Unholy itself
2. Some dynamically generated values
3. ``~/.config/unholy/Unholyfile``  (or the XDG user configuration directory)
4. ``~/.config/unholy/<project>.Unholyfile``, substituting the project name
   (again, XDG)
5. The ``Unholyfile`` from the project (either pulled from the workspace or
   from git)

Settings from lower in the list take prescedence over those higher.

``<project>.Uholyfile`` is automatically created and updated by ``unholy new``.
If Unholy needs to update it, it will do so with minimal disturbance of changes
by humans. That is, you can safely edit any Unholyfile and know that Unholy won't
wontonly discard comments, spacing, etc.

Each Unholyfile is also used for environment configuration. They are applied in the
order above--so ``core.Unholyfile`` goes first, and the repo's goes last.
