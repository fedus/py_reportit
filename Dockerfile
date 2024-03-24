# syntax=docker/dockerfile:1

FROM python:3.11-alpine

RUN apk add build-base
RUN apk add --no-cache --upgrade bash

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

RUN mkdir -p /app/photos

ENTRYPOINT [ "./run_py_reportit_crawler.sh"]
