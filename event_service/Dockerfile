FROM brisedev/event-service-dev:2.6.1

COPY ./bin/definitions.json /etc/rabbitmq/
COPY ./bin/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf

ENV RABBITMQ_LOGS=/var/log/rabbitmq/warning_log.log
EXPOSE 49153 49154 49155
