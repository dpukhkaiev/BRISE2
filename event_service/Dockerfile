FROM brisedev/event-service-dev:latest

COPY ./bin/definitions.json /etc/rabbitmq/
COPY ./bin/rabbitmq.config /etc/rabbitmq/
ENV RABBITMQ_LOGS=/var/log/rabbitmq/warning_log.log
EXPOSE 49153 49154 49155
