FROM rabbitmq:4.2.5
RUN rabbitmq-plugins enable rabbitmq_management

#enabling a management portal
RUN rabbitmq-plugins enable rabbitmq_web_stomp

RUN apt-get update && apt-get install -y -qq \
    curl=7.58.0-2ubuntu3.10 \  && apt-get -qq clean \
    && apt-get -qq autoremove \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./bin/definitions.json /etc/rabbitmq/
COPY ./bin/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf

ENV RABBITMQ_LOGS=/var/log/rabbitmq/warning_log.log
EXPOSE 49153 49154 49155
