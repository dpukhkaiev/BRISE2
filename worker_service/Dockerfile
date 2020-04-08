# Service
FROM python:3-alpine

# Installing dockerize tool
ENV DOCKERIZE_VERSION v0.6.1

RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN apk add --no-cache curl build-base && \
 pip install --upgrade pip && \
 pip install python-socketio && \
 pip install pika

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY . /usr/src/app

ARG BRISE_EVENT_SERVICE_HOST
ENV BRISE_EVENT_SERVICE_HOST ${BRISE_EVENT_SERVICE_HOST}

ARG BRISE_EVENT_SERVICE_AMQP_PORT
ENV BRISE_EVENT_SERVICE_AMQP_PORT ${BRISE_EVENT_SERVICE_AMQP_PORT}

ARG BRISE_EVENT_SERVICE_GUI_PORT
ENV BRISE_EVENT_SERVICE_GUI_PORT ${BRISE_EVENT_SERVICE_GUI_PORT}
CMD dockerize -wait http://${BRISE_EVENT_SERVICE_HOST}:${BRISE_EVENT_SERVICE_GUI_PORT} python3 -u ./intro.py
