FROM brisedev/worker-dev:latest

# create worker user
RUN useradd -ms /bin/bash w_user && echo "w_user:w_user" | chpasswd && adduser w_user sudo
COPY . /home/w_user

RUN chown -R w_user:w_user /home/w_user
USER w_user
WORKDIR /home/w_user

ARG BRISE_EVENT_SERVICE_HOST
ENV BRISE_EVENT_SERVICE_HOST ${BRISE_EVENT_SERVICE_HOST}

ARG BRISE_EVENT_SERVICE_AMQP_PORT
ENV BRISE_EVENT_SERVICE_AMQP_PORT ${BRISE_EVENT_SERVICE_AMQP_PORT}

ARG BRISE_EVENT_SERVICE_GUI_PORT
ENV BRISE_EVENT_SERVICE_GUI_PORT ${BRISE_EVENT_SERVICE_GUI_PORT}
CMD dockerize -wait http://${BRISE_EVENT_SERVICE_HOST}:${BRISE_EVENT_SERVICE_GUI_PORT}  python3.7 -u ./w_intro.py
