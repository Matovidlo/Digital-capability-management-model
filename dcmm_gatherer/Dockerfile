FROM python:alpine

RUN apk update
RUN apk add --no-cache  py-pip py3-pip build-base python3-dev libffi-dev musl-dev libressl-dev
RUN apk add --no-cache --virtual .pynacl_deps
WORKDIR /usr/src/app

COPY ./ ./
COPY requirements.txt ./

RUN python3 --version
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip install bandit jedi

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.2/wait /wait
RUN chmod +x /wait

COPY database_manipulator.py ./
CMD ["python3", "classification_scheduler.py"]

RUN bandit -f html -o result.html -r . || true

