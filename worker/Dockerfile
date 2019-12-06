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
RUN pip install -U python-socketio "python-engineio[client]" && \
    pip install -U pika

# create worker user
RUN useradd -ms /bin/bash w_user && echo "w_user:w_user" | chpasswd && adduser w_user sudo
COPY . /home/w_user

RUN chown -R w_user:w_user /home/w_user
USER w_user
WORKDIR /home/w_user

EXPOSE 8080

CMD [ "dockerize", "-wait", "http://event_service:15672", "python3.7", "-u", "./w_intro.py" ]