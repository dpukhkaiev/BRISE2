FROM rabbitmq

RUN rabbitmq-plugins enable rabbitmq_management  #enabling a management portal

RUN rabbitmq-plugins enable rabbitmq_web_stomp

RUN apt-get -qq update \
 && apt-get -qq install -y curl \
 && apt-get -qq clean \
 && apt-get -qq autoremove \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./bin/definitions.json /etc/rabbitmq/
COPY ./bin/rabbitmq.config /etc/rabbitmq/
ENV RABBITMQ_LOGS=/var/log/rabbitmq/warning_log.log
EXPOSE 49153 15672 15674
