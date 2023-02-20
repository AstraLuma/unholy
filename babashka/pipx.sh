function system.package.pipx.installed() {
  system.package python3
  system.package python3-pip
  system.package python3-venv
  system.package.pip pipx

  function is_met() {
    test -d ~/.local/pipx
  }
  function meet() {
    pipx ensurepath
  }
  process
}

function system.package.pipx() {
  local _package_name=$1; shift
  # TODO: -p (Python version) (and possibly other options)
  __babashka_log "${FUNCNAME[0]} $_package_name"

  requires system.package.pipx.installed
  function is_met() {
    # I hope this is right
    test -d ~/.local/pipx/venvs/${_package_name}
  }
  function meet() {
    pipx install ${_package_name}
  }
  process
}
