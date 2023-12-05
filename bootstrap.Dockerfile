FROM alpine
RUN apk add git docker docker-cli-compose openssh socat

CMD ["sleep", "infinity"]
