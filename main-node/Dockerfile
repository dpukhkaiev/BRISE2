FROM alpine:latest

MAINTAINER Yevhenii Semendiak <semendyak@gmail.com>

# Updating the system and adding python3
RUN apk update
RUN apk add --no-cache \
    bash \
    python3 \
    py-pip \
    py-setuptools \
    rsync \
    openssh

RUN python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

# Installing docker module
RUN pip --no-cache-dir install docker

COPY . /main-node

RUN chmod +X /main-node/configure_sshd.sh
RUN /main-node/configure_sshd.sh
EXPOSE 2222


CMD ["/usr/sbin/sshd","-D"]