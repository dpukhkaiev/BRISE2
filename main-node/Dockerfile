FROM ubuntu:16.04

MAINTAINER Yevhenii Semendiak <semendyak@gmail.com>

# Updating the system and adding python3
RUN apt-get update
RUN apt-get install -y \
    python3 \
    python3-pip \
    rsync \
    openssh-server \
    vim

# Replacing default python2 to python3
RUN pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

# Installing sklearn with needed dependencies (numpy, scipy).
RUN pip --no-cache-dir install -U scikit-learn[alldeps] sobol_seq

# Packages for API
RUN apt-get update \
    && apt-get install -y python3-pip python3-dev \
    && cd /usr/local/bin \
    && ln -s /usr/bin/python3 python \
    && python3 -m pip install requests \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install Flask \
    && python3 -m pip install flask-cors


COPY . /root

RUN chmod +x /root/configure_sshd.sh
RUN /root/configure_sshd.sh
EXPOSE 2222
EXPOSE 5000

CMD ["/usr/sbin/sshd", "-D"]
