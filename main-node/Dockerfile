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
RUN python3.7 -m pip install --upgrade Cython
RUN python3.7 -m pip install --no-cache-dir -q -r /root/requirements.txt

# Copying project
COPY . /root
RUN rm /root/Dockerfile

WORKDIR /root

CMD [ "dockerize", "-wait", "http://event_service:15672", "python3.7", "api-supreme.py"]

EXPOSE 49152
