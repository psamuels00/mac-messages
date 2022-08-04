FROM python:3.10.6

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

RUN mkdir db && ln -fs db/chat.db

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "server-run-dev.sh"]
