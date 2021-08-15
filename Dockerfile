# syntax=docker/dockerfile:1

FROM python:3.9-buster

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

RUN mkdir -p /app/photos

CMD [ "./run_py_reportit.sh"]
