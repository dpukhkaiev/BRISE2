FROM ubuntu:16.04

# Updating the system and adding python3
RUN apt-get update -qq \
    && apt-get install -y -qq apt-utils software-properties-common rsync vim

RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update -qq \
    && apt-get install -y -qq python3.7 python3-pip python3.7-dev

# Installing project requirements
COPY requirements.txt /root
RUN python3.7 -m pip install --no-cache-dir -q -r /root/requirements.txt

# Copying project
COPY . /root
RUN rm /root/Dockerfile

WORKDIR /root

EXPOSE 49152
