emanate.installed() {
  system.package.pip emanate
}

# Create is emanate's term for apply/install/etc
emanate.create() {
  # FIXME: Default _dest to ~
  while getopts "s:d:" opt; do
    case "$opt" in
      s)
        local _source=$(echo $OPTARG | xargs);;
      d)
        local _dest=$(echo $OPTARG | xargs);;
    esac
  done
  unset OPTIND
  unset OPTARG
  __babashka_log "${FUNCNAME[0]} $_source => $_dest"

  if [[ $_source == "" ]]; then
    __babashka_fail "${FUNCNAME[0]}: source directory must be set."
  fi

  local emanate_cmd="emanate create --no-confirm --source $_source --destination $_dest"

  requires emanate.installed

  function is_met() {
    local ops=$( $emanate_cmd --dry-run )
    [[ -n $ops ]]
  }
  function meet() {
    $emanate_cmd
  }
  process
}
