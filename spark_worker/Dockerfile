FROM ypandit/hdp-spark

RUN rm -fr /var/cache/yum/* && yum clean all
RUN sed -i "s/mirrorlist=https/mirrorlist=http/" /etc/yum.repos.d/epel.repo
RUN yum install -y openssh-server; yum clean all

# ssh
RUN mkdir -p /root/.ssh
RUN echo 'root:password' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
RUN echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDWQeTVRQhas0NzA/1GnrzLutDQKB+2OO5etEQQvyucSOsfzjtmkgFba5aoSJSBmUQDnfdHCb7ENvaX3B+BbobnGBGL2aQYQJXi5YBp8Z8GOTmoK3S6lCkU4DLv/eErD178sMH7w4MF1cPcU6foMLxcAMRUucXzFvz6b5bAV9N+qSGPfJVcj+XZJnIUkasA7FtovszLpnSpHNzY3S7HnnhNFS9lIvgaKTDyNuTPvKy8ChSLcyyi3KDU8YCLivUUxEN7mJfn6epgl2mFiz+c7uRiD3KVmHgH0+pij0WLi+Jw1rQuGgUSNbYMD4v2AcdsLFuKooYhXeUohGXYlWNEplK9 root@worker \
    " >> /root/.ssh/authorized_keys

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN mkdir -p /usr/src/app 
WORKDIR /usr/src/app
COPY . /usr/src/app

RUN cp /usr/lib/spark/1.3.1/conf/spark-env.sh.template /usr/lib/spark/1.3.1/conf/spark-env.sh
RUN echo 'export PYSPARK_PYTHON=/usr/bin/python2.6 \
    export PYSPARK_DRIVER_PYTHON=/usr/bin/python2.6 \
    export SPARK_YARN_USER_ENV="PYSPARK_PYTHON=/usr/bin/python2.6" \
    export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop \
    export YARN_CONF_DIR=$HADOOP_HOME/etc/hadoop' >> /usr/lib/spark/1.3.1/conf/spark-env.sh

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
