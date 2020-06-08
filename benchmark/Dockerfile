FROM ubuntu:16.04

# For changing an owner of report files
ARG host_uid
ARG host_gid
ENV host_uid=$host_uid
ENV host_gid=$host_gid

RUN groupadd -g $host_gid benchmark_user
RUN useradd -rm -s /bin/bash -g $host_gid -G sudo -u $host_uid benchmark_user
RUN usermod -aG sudo benchmark_user

RUN apt-get update && apt-get install -y -qq \
    ca-certificates=20190110~16.04.1 \
    wget=1.17.1-1ubuntu1.5 \
    xvfb=2:1.18.4-0ubuntu0.8 \
    software-properties-common=0.96.20.9 \
    && apt -qq clean \
    && apt -qq autoremove \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt -qq update && \
    apt -qq -y install python3.7-dev python3-pip

# Scripts and styles for report and plots
RUN mkdir -p /home/benchmark_user/static \
    && wget -O /home/benchmark_user/static/materialize.min.css https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css -q \
    && wget -O /home/benchmark_user/static/plotly.min.js https://cdn.plot.ly/plotly-latest.min.js -q \
    && wget -O /home/benchmark_user/static/font.woff2 https://fonts.gstatic.com/s/materialicons/v47/flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2 -q \
    # Download Orca AppImage
    && wget https://github.com/plotly/orca/releases/download/v1.2.1/orca-1.2.1-x86_64.AppImage -P /home -q \
    && chmod 777 /home/orca-1.2.1-x86_64.AppImage

# Make Orca executable under xvfb
RUN cd /home \
    && /home/orca-1.2.1-x86_64.AppImage --appimage-extract \
    && printf '#!/bin/bash \nxvfb-run --auto-servernum --server-args "-screen 0 1280x1024x24" /home/squashfs-root/app/orca "$@"' > /usr/bin/orca \
    && chmod 777 /usr/bin/orca \
    && chmod -R 777 /home/squashfs-root/

ENV LANG C.UTF-8

# Project dependencies
COPY ./benchmark/requirements.txt /home/benchmark_user/requirements.txt
RUN python3.7 -m pip install -q Cython==0.29.19
RUN python3.7 -m pip install -q -r /home/benchmark_user/requirements.txt

# Inner project dependencies
COPY ./main-node/core_entities /home/benchmark_user/core_entities/
COPY ./main-node/tools /home/benchmark_user/tools/
COPY ./main-node/logger /home/benchmark_user/logger/

# Copying common information for benchmark
COPY ./benchmark/ /home/benchmark_user/
COPY ./main-node/Resources/ /home/benchmark_user/Resources/

# Copying information for specific benchmarks, for example

# COPY ./worker/scenarios/energy_consumption/search_space_96/*.csv /home/benchmark_user/scenarios/energy_consumption/search_space_96/	
# RUN rm /home/benchmark_user/scenarios/energy_consumption/search_space_96/*avg.csv

# -     add your information here   -

# Switching user, working dir and ownership of files
WORKDIR /home/benchmark_user
RUN chown --recursive benchmark_user:benchmark_user .
USER benchmark_user

CMD [ "bash" ]
