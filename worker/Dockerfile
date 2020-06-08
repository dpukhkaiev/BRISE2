FROM python:3.7

# Updating the system
RUN echo "deb http://ftp.us.debian.org/debian sid main" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y -qq \
    gcc-8-base=8.4.0-4 \
    libmpx2=8.4.0-4 \
    libgcc-8-dev=8.4.0-4 \
    rsync=3.1.3-8 \
    vim=2:8.2.0716-3 \
    git=1:2.27.0~rc2-1 \
    unzip=6.0-25 \
# Installing Java (Open JDK) for Rapidminer and MQUAT problems
    && apt-get -y -qq install --no-install-recommends openjdk-8-jdk=8u252-b09-1 \
# Installing R and related packages for Rapidminer
    && apt-get install -y -qq r-base=4.0.0-3 && \
    Rscript -e "install.packages('data.table', repos='http://cran.rstudio.com/')" && \
    Rscript -e "install.packages('ROCR', repos='http://cran.rstudio.com/')" && \
    Rscript -e "install.packages('PRROC', repos='http://cran.rstudio.com/')" \
    && apt-get -qq clean \
    && apt-get -qq autoremove \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV JAVA_HOME="$(dirname $(dirname $(readlink -f $(which javac))))"

# Installing dockerize tool
ENV DOCKERIZE_VERSION v0.6.1

RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz

# Installing Python Socket and Pika for communication within BRISE
RUN pip install -U pika==1.1.0

# create worker user
RUN useradd -ms /bin/bash w_user && echo "w_user:w_user" | chpasswd && adduser w_user sudo
COPY . /home/w_user

RUN chown -R w_user:w_user /home/w_user
USER w_user
WORKDIR /home/w_user

ARG BRISE_EVENT_SERVICE_HOST
ENV BRISE_EVENT_SERVICE_HOST ${BRISE_EVENT_SERVICE_HOST}

ARG BRISE_EVENT_SERVICE_AMQP_PORT
ENV BRISE_EVENT_SERVICE_AMQP_PORT ${BRISE_EVENT_SERVICE_AMQP_PORT}

ARG BRISE_EVENT_SERVICE_GUI_PORT
ENV BRISE_EVENT_SERVICE_GUI_PORT ${BRISE_EVENT_SERVICE_GUI_PORT}
CMD dockerize -wait http://${BRISE_EVENT_SERVICE_HOST}:${BRISE_EVENT_SERVICE_GUI_PORT}  python3.7 -u ./w_intro.py
