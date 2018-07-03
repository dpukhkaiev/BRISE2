FROM ubuntu:16.04

MAINTAINER Roman Kosovnenko <pariom18 @gmail.com>

RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip
RUN pip3 install Flask
RUN apt-get install -y r-base

RUN mkdir -p /usr/src/app 
RUN Rscript -e "install.packages('data.table', repos='http://cran.rstudio.com/')"
RUN Rscript -e "install.packages('ROCR', repos='http://cran.rstudio.com/')"
RUN Rscript -e "install.packages('PRROC', repos='http://cran.rstudio.com/')"
RUN \
    echo "===> add webupd8 repository..."  && \
    echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main" | tee /etc/apt/sources.list.d/webupd8team-java.list  && \
    echo "deb-src http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main" | tee -a /etc/apt/sources.list.d/webupd8team-java.list  && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886  && \
    apt-get update

RUN \
    echo "===> install Java"  && \
    echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections  && \
    echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections  && \
    DEBIAN_FRONTEND=noninteractive  apt-get install -y --force-yes oracle-java8-installer oracle-java8-set-default

RUN \
    echo "===> clean up..."  && \
    rm -rf /var/cache/oracle-jdk8-installer


COPY rapidminer-studio/ /root/rapidminer-studio/
COPY .RapidMiner/ /root/.RapidMiner/
COPY .RapidMiner/ /home/pariom/.RapidMiner/
COPY swc-data/ /root/swc-data/
# COPY ./configure_sshd.sh /root/
COPY csv_data/ /usr/src/app/csv_data/
COPY config.json /usr/src/app/
COPY w_server.py /usr/src/app/
COPY server.py.bak /usr/src/app/
COPY worker.py /usr/src/app/


# RUN chmod +x /root/configure_sshd.sh
# RUN /root/configure_sshd.sh
WORKDIR /usr/src/app


EXPOSE 8080
CMD [ "python", "-u", "./w_server.py" ]