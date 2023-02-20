FROM ghcr.io/astraluma/babashka:system

COPY babashka /etc/babashka
RUN babashka -d /etc/babashka dev-environment
