#!/usr/bin/env bash

# Output colors
NORMAL="\\033[0;39m"
RED="\\033[1;31m"
BLUE="\\033[1;34m"

# Names to identify images and containers of this app
IMAGE_NAME='bench'
CONTAINER_NAME="bench_1"

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
  echo "   > build - To build the Docker image"
  echo "   > run - Create a new container of an image"
  echo "   > up - Remove, build and run"
  echo "   > restart - Remove the container, and run"
  echo "   > extract - Copy experiments dump files from the container to host"
  echo "   > stop - Stop the container"
  echo "   > start - Start the container"
  echo "   > bash - Log host into the container"
  echo "   > remove - Remove the container and the image"
  echo "   > help - Display this help"
  echo -e -n "$NORMAL"
  echo "-----------------------------------------------------------------------"

}

build() {
  cd .. 
  docker build -t $IMAGE_NAME --build-arg host_uid=$(id -u) --build-arg host_gid=$(id -g) --rm -f "benchmark/dockerfile" .
  cd benchmark

  [ $? != 0 ] && error "Docker image build failed !" && exit 100
}

run() {
  log "Run benchmark"
  mkdir -p ./results/serialized/ ./results/reports/
  docker run -it --name="$CONTAINER_NAME" -v $(pwd):/app/volume $IMAGE_NAME
  
  [ $? != 0 ] && error "Container run failed!" && exit 105
}

up() {
  echo "Installing"
  remove
  build
  run
}
restart() {
  echo "Restart"
  docker rm -f $CONTAINER_NAME &> /dev/null || true
  run
}

extract() {
  echo "Extract dump files from experiment"
  mkdir -p ./results/serialized/
  docker cp main-node:/root/Results/serialized/. ./results/serialized

  [ $? != 0 ] && error "docker cp comand failed" && exit 1
}

bash() {
  log "BASH"
  docker run -it --rm -v $(pwd):/app $IMAGE_NAME /bin/bash
}

stop() {
  docker stop $CONTAINER_NAME
}

start() {
  docker start $CONTAINER_NAME
}

remove() {
  log "Removing previous container $CONTAINER_NAME and image $IMAGE_NAME" && \
    docker rm -f $CONTAINER_NAME &> /dev/null || true && \
    docker rmi $IMAGE_NAME &> /dev/null || true
}

if [ -z ${1}  ]; then
  help
fi

$*