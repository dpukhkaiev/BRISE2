FROM python:3.7

# Updating the system
RUN echo "deb http://ftp.us.debian.org/debian sid main" >> /etc/apt/sources.list \
    && apt-get update -qq \
    && apt-get install -y -qq rsync vim git unzip \

# Installing Java (Open JDK) for MQUAT problems
    && apt-get -y -qq install --no-install-recommends openjdk-8-jdk

ENV JAVA_HOME="$(dirname $(dirname $(readlink -f $(which javac))))"

# Installing dockerize tool
ENV DOCKERIZE_VERSION v0.6.1

RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz

# Installing Python Socket and Pika for communication within BRISE
RUN pip install -U pika

# ssh
RUN mkdir -p /root/.ssh
COPY ./.ssh/ /root/.ssh/
RUN touch /root/.ssh/known_hosts && chown -v root /root/.ssh/known_hosts
RUN chmod 700 /root/.ssh && \
    chmod 600 /root/.ssh/id_rsa && \
    chmod 644 /root/.ssh/id_rsa.pub && \
    chmod 777 /root/.ssh/known_hosts

RUN mkdir -p /usr/src/app 
WORKDIR /usr/src/app

COPY . /usr/src/app

EXPOSE 8080

CMD [ "dockerize", "-wait", "http://event_service:15672", "python3.7", "-u", "./w_intro.py" ]
