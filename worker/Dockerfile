FROM ubuntu:16.04

# Updating the system and adding python3
RUN apt-get update \
    && apt-get install -y python3 \
    && apt-get install -y    python3-pip \
    && apt-get install -y    rsync \
    && apt-get install -y    vim \
    && apt-get install -y    r-base

# Replacing default python2 to python3
RUN pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

RUN pip install --upgrade pip && \
    pip install -U python-socketio && \
    pip install -U "python-engineio[client]"

# Install Java (Open JDK)
RUN apt-get update && \
    apt-get -y install unzip openjdk-8-jdk

# Export some environment variables
ENV PATH=$PATH:$GRADLE_HOME/bin JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

# install R packages
RUN Rscript -e "install.packages('data.table', repos='http://cran.rstudio.com/')"
RUN Rscript -e "install.packages('ROCR', repos='http://cran.rstudio.com/')"
RUN Rscript -e "install.packages('PRROC', repos='http://cran.rstudio.com/')"

# create worker user
RUN useradd -ms /bin/bash w_user && echo "w_user:w_user" | chpasswd && adduser w_user sudo
COPY . /home/w_user     

RUN chown -R w_user:w_user /home/w_user
USER w_user
WORKDIR /home/w_user

EXPOSE 8080

CMD [ "python3", "-u", "./w_intro.py" ]