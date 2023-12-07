# Show this help
help:
  just --list

# Run lint tools
lint:
  poetry run flake8 unholy

# Build the bootstrap container
build-bootstrap:
  docker build -f bootstrap.Dockerfile -t ghcr.io/astraluma/unholy/bootstrap:nightly .

# Run docs commands
docs *ARGS:
  poetry run make -C docs {{ARGS}}
