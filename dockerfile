FROM alpine AS build-env
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
RUN apk update\
    && apk add --no-cache python