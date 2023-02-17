FROM ghcr.io/astraluma/babashka:master

COPY babashka /etc/babashka
RUN babashka -d /etc/babashka dev-environment
