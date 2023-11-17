# Show this help
help:
  just --list

# Build the bootstrap container
build-bootstrap:
  docker build -f bootstrap.Dockerfile -t ghcr.io/astraluma/unholy/bootstrap:nightly .
