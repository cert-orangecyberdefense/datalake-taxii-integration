FROM python:3.8-alpine

RUN apk add --no-cache g++ gcc libxslt-dev

WORKDIR /code



ADD ./requirements.txt /code/requirements.txt

RUN pip install -r requirements.txt

ADD . /code

RUN mkdir /code/output

RUN chown -R 1001:1001 /code
RUN chown -R 1001:1001 /code/output

USER 1001

ENTRYPOINT ["python", "main.py"]
