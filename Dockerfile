FROM python:alpine

RUN apk add --no-cache g++ gcc libxslt-dev

WORKDIR /code

ADD ./requirements.txt /code/requirements.txt

RUN pip install -r requirements.txt

ADD . /code

RUN chown -R 1001:1001 /code

USER 1001

ENTRYPOINT ["python", "main.py"]
