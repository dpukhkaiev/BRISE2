FROM python:3.7

# Updating the system
RUN echo "deb http://ftp.us.debian.org/debian sid main" >> /etc/apt/sources.list && \
    apt-get update -qq && \
    apt-get install -y -qq rsync vim git unzip

# Installing Python Socket for communication within BRISE
RUN pip install -U python-socketio "python-engineio[client]"

# Installing Java (Open JDK) for Rapidminer and MQUAT problems
RUN apt-get -y -qq install --no-install-recommends openjdk-8-jdk
ENV JAVA_HOME="$(dirname $(dirname $(readlink -f $(which javac))))"

# Installing R and related packages for Rapidminer
RUN apt-get install -y -qq r-base && \
    Rscript -e "install.packages('data.table', repos='http://cran.rstudio.com/')" && \
    Rscript -e "install.packages('ROCR', repos='http://cran.rstudio.com/')" && \
    Rscript -e "install.packages('PRROC', repos='http://cran.rstudio.com/')"

# create worker user
RUN useradd -ms /bin/bash w_user && echo "w_user:w_user" | chpasswd && adduser w_user sudo
COPY . /home/w_user

RUN chown -R w_user:w_user /home/w_user
USER w_user
WORKDIR /home/w_user

EXPOSE 8080

CMD [ "python3.7", "-u", "./w_intro.py" ]