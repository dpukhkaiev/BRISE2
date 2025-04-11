FROM brisedev/benchmark-dev:2.6.0

# Inner project dependencies
COPY ./main_node/core_entities /home/benchmark_user/core_entities/
COPY ./main_node/tools /home/benchmark_user/tools/
COPY ./main_node/logger /home/benchmark_user/logger/

# Copying common information for benchmark
COPY ./benchmark/ /home/benchmark_user/
COPY ./main_node/Resources/ /home/benchmark_user/Resources/

# For changing an owner of report files
ARG host_uid
ARG host_gid
ENV host_uid=$host_uid
ENV host_gid=$host_gid

# Comment this line for Apple devices
#RUN groupadd -g $host_gid benchmark_user
RUN useradd -rm -s /bin/bash benchmark_user
RUN usermod -aG sudo benchmark_user

# Copying information for specific benchmarks, for example

#COPY ./worker/scenarios/energy_consumption/search_space_96/*.csv /home/benchmark_user/scenarios/energy_consumption/search_space_96/
#RUN rm /home/benchmark_user/scenarios/energy_consumption/search_space_96/*avg.csv

# -     add your information here   -

# Switching user, working dir and ownership of files
WORKDIR /home/benchmark_user
RUN chown --recursive benchmark_user:benchmark_user .
USER benchmark_user

RUN echo "conda activate brise-260" >> ~/.bashrc
CMD conda run -n brise-260 python3 ./entrypoint.py $MODE