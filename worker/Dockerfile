FROM ubuntu:16.04

# Updating the system and adding python3
RUN apt-get update \
    && apt-get install -y python3 \
    && apt-get install -y    python3-pip \
    && apt-get install -y    rsync \
    && apt-get install -y    vim

# Replacing default python2 to python3
RUN pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

RUN mkdir -p /usr/src/app 
WORKDIR /usr/src/app

RUN pip install --upgrade pip && \
pip install -U python-socketio && \
pip install -U "python-engineio[client]"

# Install Java (Open JDK)
RUN apt-get update && \
    apt-get -y install unzip openjdk-8-jdk

# Export some environment variables
ENV PATH=$PATH:$GRADLE_HOME/bin JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

COPY . /usr/src/app

EXPOSE 8080

CMD [ "python3", "-u", "./w_intro.py" ]