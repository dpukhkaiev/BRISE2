FROM brisedev/benchmark-dev:2.5.0

# For changing an owner of report files
ARG host_uid
ARG host_gid
ENV host_uid=$host_uid
ENV host_gid=$host_gid

RUN groupadd -g $host_gid benchmark_user
RUN useradd -rm -s /bin/bash -g $host_gid -G sudo -u $host_uid benchmark_user
RUN usermod -aG sudo benchmark_user

# Inner project dependencies
COPY ./main_node/core_entities /home/benchmark_user/core_entities/
COPY ./main_node/tools /home/benchmark_user/tools/
COPY ./main_node/logger /home/benchmark_user/logger/
COPY ./main_node/selection /home/benchmark_user/selection/

# Copying common information for benchmark
COPY ./benchmark/ /home/benchmark_user/
COPY ./main_node/Resources/ /home/benchmark_user/Resources/

# Copying information for specific benchmarks, for example

#COPY ./worker/scenarios/energy_consumption/search_space_96/*.csv /home/benchmark_user/scenarios/energy_consumption/search_space_96/
#RUN rm /home/benchmark_user/scenarios/energy_consumption/search_space_96/*avg.csv

# -     add your information here   -

# Switching user, working dir and ownership of files
WORKDIR /home/benchmark_user
RUN chown --recursive benchmark_user:benchmark_user .
USER benchmark_user

CMD [ "bash" ]
