FROM alpine
RUN apk add git docker docker-cli-compose

CMD ["sleep", "infinity"]
