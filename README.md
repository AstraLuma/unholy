# unholy

Cooperates with Docker Compose, injects an nvim-based container
into it, and connects neovide to it.

You can call it what you'd like, but I'm going to call this union `unholy`.

## Requirements

- Unholy itself (I suggest using [pipx](https://pypa.github.io/pipx/))
- Git
- The Docker CLI
- [Neovide](https://neovide.dev/)

## Usage

1. Commit an Unholyfile to your repo (see below)
2. Run `unholy new <git url>`
3. Work on your project using `unholy shell` and `unholy neovide`

Use `unholy remake` to rebuild your development environment without
re-cloning your repo or touching your work.

Note: By default, the name of the Unholy project is the repo name.

## Unholyfile

A major aspect of unholy is the Unholyfile. It is a script with
[TOML](https://toml.io/en/) head matter, like so:

```
---
[dev]
image="python"
---
pip install pytest
```

The complete headmatter schema is loosely documented in [core.Unholyfile](unholy/core.Unholyfile).

The script supports a `#!`, defaulting to `#!/bin/sh`

If you specify a non-default image, it must be Debian-based.

## Additional config

Local configuration (including project definitions) are stored in the XDG
Config directory (default `~/.config/unholy`).

There is a global `~/.config/unholy/Unholy` applied to all projects. This is
an excellent place for personal settings (like utilities you like or nvim
configuration).

Each project gets an `~/.config/<name>.Unholyfile` where unholy keeps git and
Docker settings. You can add some local project overrides here.
