FROM alpine
RUN apk add git docker docker-cli-compose openssh

CMD ["sleep", "infinity"]
