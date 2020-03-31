
FROM python:3.8-slim-buster

ENV LISTEN_PORT=8000
EXPOSE 8000

COPY /app /app

COPY requirements.txt /

RUN pip install --upgrade wheel
RUN pip install -r requirements.txt


WORKDIR /app
ENTRYPOINT [ "python" ]
CMD [ "main.py" ]

