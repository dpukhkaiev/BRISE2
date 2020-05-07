FROM ubuntu:16.04

# Updating the system and adding python3
RUN apt-get update -qq \
    && apt-get install -y -qq software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update -qq \
    && apt-get install -y -qq apt-utils rsync vim \
    && apt-get install -y -qq python3.7 python3-pip python3.7-dev wget \
    && apt-get -qq clean \
    && apt-get -qq autoremove \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Installing dockerize tool
ENV DOCKERIZE_VERSION v0.6.1

RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz

# Installing project requirements
COPY requirements.txt /root
RUN python3.7 -m pip install -q Cython
RUN python3.7 -m pip install --no-cache-dir -q -r /root/requirements.txt

# Copying project
COPY . /root
RUN rm /root/Dockerfile

WORKDIR /root

ARG BRISE_EVENT_SERVICE_HOST
ENV BRISE_EVENT_SERVICE_HOST ${BRISE_EVENT_SERVICE_HOST}

ARG BRISE_EVENT_SERVICE_AMQP_PORT
ENV BRISE_EVENT_SERVICE_AMQP_PORT ${BRISE_EVENT_SERVICE_AMQP_PORT}

ARG BRISE_EVENT_SERVICE_GUI_PORT
ENV BRISE_EVENT_SERVICE_GUI_PORT ${BRISE_EVENT_SERVICE_GUI_PORT}

ARG BRISE_DATABASE_HOST
ENV BRISE_DATABASE_HOST ${BRISE_DATABASE_HOST}

ARG BRISE_DATABASE_PORT
ENV BRISE_DATABASE_PORT ${BRISE_DATABASE_PORT}

ARG BRISE_DATABASE_NAME
ENV BRISE_DATABASE_NAME ${BRISE_DATABASE_NAME}

ARG BRISE_DATABASE_USER
ENV BRISE_DATABASE_USER ${BRISE_DATABASE_USER}

ARG BRISE_DATABASE_PASS
ENV BRISE_DATABASE_PASS ${BRISE_DATABASE_PASS}

CMD dockerize -wait http://${BRISE_EVENT_SERVICE_HOST}:${BRISE_EVENT_SERVICE_GUI_PORT}  python3.7 -u api-supreme.py
