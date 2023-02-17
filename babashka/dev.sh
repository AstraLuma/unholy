nvim_installed() {
    # Debian, Ubuntu, Fedora, Homebrew
    system.package neovim
    # Debian, Ubuntu, Fedora (Unneeded in Homebrew)
    # system.package python3-neovim
}

astronvim_installed() {
  local ABSOLUTE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  requires nvim_installed

  system.directory.git ~/.config/nvim \
    -s https://github.com/AstroNvim/AstroNvim

  system.directory ~/.config/nvim/lua/user
  # Maybe someday template this
  system.file ~/.config/nvim/lua/user/init.lua \
    -s ${ABSOLUTE_PATH}/astronvim-config.lua

  function is_met() {
    test -f ~/.config/nvim/lua/packer_compiled.lua
  }
  function meet() {
    nvim --headless -c 'autocmd User PackerComplete quitall'
  }
  process
}

dev-environment() {
  # NeoVim
  requires nvim_installed
  requires astronvim_installed
  # TODO: Clipboard

  system.package.pipx.installed

  # Tools for people
  sysem.package git # I'm just assuming this name is universal
  system.package ripgrep  # Debian, Ubuntu, Fedora, Homebrew

  # Language support
  system.package.pipx pyright

  # TODO: Emanate
}
