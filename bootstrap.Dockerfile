FROM alpine
RUN apk install git docker

CMD ["sleep", "infinity"]
