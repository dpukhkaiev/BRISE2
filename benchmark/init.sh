#!/usr/bin/env bash

# Output colors
NORMAL="\\033[0;39m"
RED="\\033[1;31m"
BLUE="\\033[1;34m"

# Names to identify images and containers of this app
IMAGE_NAME="brise-benchmark_image"
CONTAINER_NAME="brise-benchmark"
BRISE_NETWORK="brise_network"

HOMEDIR="/home/$USER"
EXECUTE_AS="sudo -u $USER HOME=$HOME_DIR"
SCRIPT_DIR=$(dirname "${BASH_SOURCE}")


log() {
  echo -e "$BLUE > $1 $NORMAL"
}

error() {
  echo ""
  echo -e "$RED >>> ERROR - $1$NORMAL"
}

help() {
  echo "-----------------------------------------------------------------------"
  echo "                      Available commands                              -"
  echo "-----------------------------------------------------------------------"
  echo -e -n "$BLUE"
  echo "   > up - Executes 'build_image' and 'run_container' commands. 'run_container' requires parameter 'benchmark' or 'analyse' to run the benchmark or analyse the results."
  echo "   > down - 'remove_container' and 'remove_image'."
  echo "   > restart - 'down' and 'up'."
  echo "   > build_image - Build the Docker image of benchmark container."
  echo "   > run_container - Create and run new container based on an image. "
  echo "   > remove_image - Remove the image."
  echo "   > remove_container - Remove the container."
  echo "   > bash - Attach bash console from benchmark container."
  echo "   > rate - Display how many Experiments were performed hourly since startup."
  echo "   > help - Display this help message."
  echo -e -n "$NORMAL"
  echo "-----------------------------------------------------------------------"

}

up() {
  log "Starting for ${1}"
  build_image || true && \
  run_container ${1}

}

down() {
  log "Removing previous container $CONTAINER_NAME and image $IMAGE_NAME"
  remove_container || true && \
  remove_image || true

}

restart(){
    log "Restarting for ${1}"
    down
    up ${1}
}

build_image() {
  log "Building Benchmark image."
  cd .. 
  docker build -t $IMAGE_NAME --build-arg host_uid=$(id -u) --build-arg host_gid=$(id -g) --rm -f "benchmark/dockerfile" .
  cd benchmark

  [ $? != 0 ] && error "Docker image build failed !" && exit 100
  log "Done!"
}

run_container() {
  log "Running benchmark.py script with '${1}' parameter in the $CONTAINER_NAME container."
  mkdir -p ./results/serialized/ ./results/reports/
  docker run -it --name="$CONTAINER_NAME" -v $(pwd)/results:/home/benchmark_user/results:z --network=$BRISE_NETWORK $IMAGE_NAME /usr/bin/python3 benchmark.py ${1}

  [ $? != 0 ] && error "Container run failed!" && exit 105
}

remove_container(){
  log "Removing container $CONTAINER_NAME."
  docker rm -f $CONTAINER_NAME &> /dev/null
  log "Done!"

}

remove_image() {
  log "Removing image $IMAGE_NAME."
  docker rmi $IMAGE_NAME &> /dev/null
  log "Done!"
}

bash() {
  log "executing BASH"
  execute_command_in_container "/bin/bash"
}

execute_command_in_container(){
  if [ "$(docker ps -a | grep $CONTAINER_NAME)" ]
    then
    # container exists
        if [ $(docker inspect -f '{{.State.Running}}' $CONTAINER_NAME) == "true" ]
         then
            # container is running - execute in running container
            docker exec -it "$CONTAINER_NAME" ${1}
        else
            # container stopped - start container again and run a command
            docker commit $CONTAINER_NAME $IMAGE_NAME
            docker rm $CONTAINER_NAME
            docker run -it -v $(pwd)/results:/home/benchmark_user/results:z --name=$CONTAINER_NAME $IMAGE_NAME ${1}
        fi
    else
        # container does not exist - create container and run a command
        docker run -it --rm -v $(pwd)/results:/home/benchmark_user/results:z --name=$CONTAINER_NAME $IMAGE_NAME ${1}
    fi
}

rate(){
    log "executing check_file_appearance_rate under ./results/serialized folder"
    execute_command_in_container "/usr/bin/python3 shared_tools.py"
}

if [ -z ${1}  ]; then
  help
fi

$*
unset -f execute_command_in_container