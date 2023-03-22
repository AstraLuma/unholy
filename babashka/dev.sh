function system.package.url() {
  local _package_name=$1; shift
  local _package_url=$1; shift

  local _download_path=/tmp/$(basename $_package_url)

  system.package curl
  
  # Any flags you want to set should be set via apt_flags= outside this
  # function call
  __babashka_log "${FUNCNAME[0]} (apt) $_package_name"
   function is_met() {
     dpkg -s ${apt_pkg:-$_package_name} 2>&1 > /dev/null
   }
   function meet() {
     [ -n "$__babushka_force" ] && apt_flags="${apt_flags} -f --force-yes"
     curl -Lo $_download_path $_package_url
     DEBIAN_FRONTEND=noninteractive $__babashka_sudo apt-get -yqq install $apt_flags $_download_path
   }
  process
}

nvim_installed() {
    # Debian, Ubuntu, Fedora, Homebrew
    system.package.url neovim https://github.com/neovim/neovim/releases/download/stable/nvim-linux64.deb
    # Debian, Ubuntu, Fedora (Unneeded in Homebrew)
    # system.package python3-neovim
}

astronvim_installed() {
  local ABSOLUTE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  requires nvim_installed

  system.directory.git ~/.config/nvim \
    -s https://github.com/AstroNvim/AstroNvim.git

  system.directory ~/.config/nvim/lua/user
  # Maybe someday template this
  system.file ~/.config/nvim/lua/user/init.lua \
    -s ${ABSOLUTE_PATH}/astronvim-config.lua

  function is_met() {
    test -e ~/.local/state/nvim/lazy
  }
  function meet() {
    nvim --headless -c 'autocmd User LazyDone quitall' < /dev/null
  }
  process
}

just_installed() {
   function is_met() {
     test -e /usr/local/bin/just
   }
   function meet() {
     curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin
   }
  process
}

dev-environment() {
  system.package git # I'm just assuming this name is universal
  system.package npm

  # NeoVim
  requires nvim_installed
  requires astronvim_installed
  # TODO: Clipboard

  system.package.pipx.installed

  # Tools for people
  system.package ripgrep  # Debian, Ubuntu, Fedora, Homebrew
  
  requires just_installed

 # TODO: Emanate
}
