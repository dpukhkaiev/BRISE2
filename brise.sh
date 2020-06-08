#!/bin/bash

# Output colors
NORMAL="\\033[0;39m"
RED="\\033[1;31m"
BLUE="\\033[1;34m"

N_workers=1
command=
mode=
event_service_host=
services=("main-node" "event_service" "worker_service" "front-end" "worker")
database=BRISE_db


log() {
  echo -e "$BLUE > $1 $NORMAL"
}

error() {
  echo ""
  echo -e "$RED >>> ERROR - $1$NORMAL"
}

help() {
  echo "-----------------------------------------------------------------------"
  echo "-                 BRISE deployment control script                      -"
  echo "-                                                                     -"
  echo "-                      Available commands:                             -"
  echo "-----------------------------------------------------------------------"
  echo -e -n "$BLUE"
  echo "   > up - Starts specified services. By default starts all services by using docker-compose."
  echo "        Required parameter:"
  echo "        --mode or -m: A required parameter that specifies running mode. "
  echo "                * docker-compose:  Running services locally by docker-compose"
  echo "                * k8s:  Building new images based on local services description files and running them under Kubernetes control"
  echo "        Optional parameters: "
  echo "        --event_service_host or -e: A parameter that overrides the hostname/IP of an event service."
  echo "                                    By default equal the 'General.EventService.Address' in 'main_node/Resources/SettingsBRISE.json'"
  echo "        --event_service_AMQP_port or -eAMQP: A parameter that overrides the AMQP port of an event service."
  echo "                                    By default equal the 'General.EventService.AMQTPort' in 'main_node/Resources/SettingsBRISE.json'"
  echo "        --event_service_GUI_port or -eGUI: A parameter that overrides the GUI port of an event service."
  echo "                                    By default equal the 'General.EventService.GUIPort' in 'main_node/Resources/SettingsBRISE.json'"
  echo "        --database_host or -db_host: A parameter that overrides the hostname/IP of a BRISE database."
  echo "                                    By default equal the 'General.Database.Address' in 'main_node/Resources/SettingsBRISE.json'"
  echo "        --database_port or -db_port: A parameter that overrides the port of a BRISE database."
  echo "                                    By default equal the 'General.Database.Port' in 'main_node/Resources/SettingsBRISE.json'"
  echo "        --database_name or -db_name: A parameter that overrides the name of a BRISE database."
  echo "                                    By default equal the 'General.Database.DatabaseName' in 'main_node/Resources/SettingsBRISE.json'"
  echo "        --database_user or -db_user: A parameter that overrides the username of a BRISE database."
  echo "                                    By default equal the 'General.Database.DatabaseUser' in 'main_node/Resources/SettingsBRISE.json'"
  echo "        --database_pass or -db_pass: A parameter that overrides the password of a BRISE database user."
  echo "                                    By default equal the 'General.Database.DatabasePass' in 'main_node/Resources/SettingsBRISE.json'"
  echo "        --workers or -w: A parameter that overrides the number of workers."
  echo "                                    By default equal the 'General.NumberOfWorkers' in 'main_node/Resources/SettingsBRISE.json'"
  echo "        --k8s_docker_hub_name or -k8s_d_n: A parameter to specify the docker hub name that is used by Kubernetes for deployment."
  echo "                                    By default equals to 'master-node'. "
  echo "        --k8s_docker_hub_port or -k8s_d_p: A parameter to specify the local docker hub port that is used by Kubernetes."
  echo "                                    By default equal '5000' "
  echo "        --services or -s: List all services that will start. Have to be at the end of the command."
  echo
  echo "   > down - Stops all BRISE services on the machine/cluster"
  echo "        Required parameter:"
  echo "        --mode or -m: A required parameter that specifies stopping mode. "
  echo "                * docker-compose:  Stopping services locally by docker-compose"
  echo "                * k8s:  Stopping and deleting all services and deployments under Kubernetes control"
  echo
  echo "   > restart - 'down' and 'up'."
  echo
  echo "   > clean_database - Cleans the BRISE database."
  echo "        Optional parameter:"
  echo "        --database or -db: A parameter that overwrites the default name of the BRISE database to be cleaned. The default name is 'BRISE_db'"
  echo
  echo "   > help - Display this help message."
  echo -e -n "$NORMAL"
  echo "-----------------------------------------------------------------------"
  echo "- For more information refer to https://github.com/dpukhkaiev/BRISE2 -"
  echo "-----------------------------------------------------------------------"

}

up() {
  if [[ "${mode}" == "docker-compose" ]]; then
        log "Building and deploying BRISE to docker-compose."
        docker-compose build --build-arg BRISE_EVENT_SERVICE_HOST="${event_service_host}" \
                             --build-arg BRISE_EVENT_SERVICE_AMQP_PORT="${event_service_AMQP_port}"\
                             --build-arg BRISE_EVENT_SERVICE_GUI_PORT="${event_service_GUI_port}"\
                             --build-arg BRISE_DATABASE_HOST="${database_host}" \
                             --build-arg BRISE_DATABASE_PORT="${database_port}" \
                             --build-arg BRISE_DATABASE_NAME="${database_name}" \
                             --build-arg BRISE_DATABASE_USER="${database_user}" \
                             --build-arg BRISE_DATABASE_PASS="${database_pass}" \
                              ${services[*]}
        log "Starting ${services[*]}"
        docker-compose up -d --scale worker=${N_workers} ${services[*]}
  elif  [[ "${mode}" == "k8s" ]]; then
        log "Building and starting BRISE K8s deployment based on local service description files."
        for service in "${services[@]}"; do
             if [[ "${service}" != "mongo-db" ]]; then
                docker build --tag "${service}_image" --build-arg BRISE_EVENT_SERVICE_HOST="${event_service_host}"\
                                                    --build-arg BRISE_EVENT_SERVICE_AMQP_PORT="${event_service_AMQP_port}"\
                                                    --build-arg BRISE_EVENT_SERVICE_GUI_PORT="${event_service_GUI_port}"\
                                                    --build-arg BRISE_DATABASE_HOST="${database_host}" \
                                                    --build-arg BRISE_DATABASE_PORT="${database_port}" \
                                                    --build-arg BRISE_DATABASE_NAME="${database_name}" \
                                                    --build-arg BRISE_DATABASE_USER="${database_user}" \
                                                    --build-arg BRISE_DATABASE_PASS="${database_pass}" \
                                                        "./${service}/"
                docker tag "${service}_image:latest" "${k8s_docker_hub_name}:${k8s_docker_hub_port}/local/${service}_image"
                docker push "${k8s_docker_hub_name}:${k8s_docker_hub_port}/local/${service}_image"
             fi
             kubectl create -f "./K8s/${service}-deployment.yaml"
             if [[ "${k8s_docker_hub_name}" != "master-node" ]] || [[ "${k8s_docker_hub_port}" != "5000" ]]; then
                if [[ "${service}" != "mongo-db" ]]; then
                    kubectl set image "deployment.apps/${service//[_]/-}" "*=${k8s_docker_hub_name}:${k8s_docker_hub_port}/local/${service}_image"
                fi
             fi
             if [[ "${service}" == "worker" ]]; then
                  kubectl scale deployment.apps/worker --replicas=${N_workers}
             elif [[ "${service}" == "event_service" ]]; then
                  kubectl create -f ./K8s/event_service-service-NodePort.yaml
             elif [[ "${service}" == "front-end" ]]; then
                  kubectl create -f ./K8s/front-end-service-NodePort.yaml
             elif [[ "${service}" == "mongo-db" ]]; then
                  kubectl create -f ./K8s/mongo-db-service-NodePort.yaml
             fi
        done
  else
        error "Wrong mode."
        help
  fi
}

down() {
  if [[ "${mode}" == "docker-compose" ]]; then
        log "Stopping docker-compose deployment of BRISE services: ${services[*]}."
        docker-compose down
   elif  [[ "${mode}" == "k8s" ]]; then
        log "Stopping K8s deployment of BRISE services: ${services[*]}."
        for service in "${services[@]}"; do
             kubectl delete -f "./K8s/${service}-deployment.yaml"
             if [[ "${service}" == "event_service" ]]; then
                kubectl delete -f ./K8s/event_service-service-NodePort.yaml
             fi
             if [[ "${service}" == "front-end" ]]; then
                kubectl delete -f ./K8s/front-end-service-NodePort.yaml
             fi
             if [[ "${service}" == "mongo-db" ]]; then
                kubectl delete -f ./K8s/mongo-db-service-NodePort.yaml
             fi
        done
   else
        error "Wrong mode"
        help
   fi
}

restart(){
    log "Restarting ${services[@]}"
    down
    up
}

dependency_check(){
    if ! command -v jq >/dev/null 2>&1 ; then
        error "Please install the required package jq"
        exit
    fi
    if ! command -v docker >/dev/null 2>&1 ; then
        error "Please install the required package docker"
        exit
    fi

    if [[ "${mode}" == "k8s" ]]; then
        if ! command -v kubectl >/dev/null 2>&1 ; then
        error "Please install the required package kubectl"
        exit
        fi
    fi
    if [[ "${mode}" == "docker-compose" ]]; then
        if ! command -v docker-compose >/dev/null 2>&1 ; then
        error "Please install the required package docker-compose"
        exit
        fi
    fi
}

clean_database() {
    container_name=mongo-db
    container_prev_state=

    if [[ $(docker ps --filter "name=^/$container_name$" --format '{{.Names}}') == $container_name ]]; then
        container_prev_state=1
    else
        container_prev_state=0
        docker-compose up -d --build mongo-db
    fi

    while true; do
        sleep 1
        docker exec -it -i mongo-db mongo $database --eval "db.serverStatus()" > /dev/null 2>&1 == 0 || break
    done

    docker exec -it -i mongo-db mongo $database --eval "db.dropDatabase();"

    if [[ $container_prev_state == 0 ]]; then
        docker-compose stop mongo-db
    fi
}

if [[ -z ${1}  ]]; then
  help
else
    dependency_check
    N_workers=$( cat main-node/Resources/SettingsBRISE.json | jq -r '.General.NumberOfWorkers' )
    event_service_host=$( cat main-node/Resources/SettingsBRISE.json | jq -r '.General.EventService.Address' )
    event_service_AMQP_port=$( cat main-node/Resources/SettingsBRISE.json | jq -r '.General.EventService.AMQTPort' )
    event_service_GUI_port=$( cat main-node/Resources/SettingsBRISE.json | jq -r '.General.EventService.GUIPort' )
    database_host=$( cat main-node/Resources/SettingsBRISE.json | jq -r '.General.Database.Address' )
    database_port=$( cat main-node/Resources/SettingsBRISE.json | jq -r '.General.Database.Port' )
    database_name=$( cat main-node/Resources/SettingsBRISE.json | jq -r '.General.Database.DatabaseName' )
    database_user=$( cat main-node/Resources/SettingsBRISE.json | jq -r '.General.Database.DatabaseUser' )
    database_pass=$( cat main-node/Resources/SettingsBRISE.json | jq -r '.General.Database.DatabasePass' )
    k8s_docker_hub_name='master-node'
    k8s_docker_hub_port='5000'

    command=$1
    shift

    while [[ "$1" != "" ]]; do
        case $1 in
            -m | --mode )
                shift
                mode=$1
                if [[ "${mode}" != "docker-compose" ]] && [[ "${mode}" != "k8s" ]]; then
                    error "Wrong parameter --mode (-m)"
                    help
                    exit 1
                fi
                ;;

            -e | --event_service_host )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]]; then
                    event_service_host=$1
                else
                    error "Wrong parameter --event_service_host (-e)"
                    help
                    exit 1
                fi
                ;;

            -eAMQP | --event_service_AMQP_port )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]]; then
                    event_service_AMQP_port=$1
                else
                    error "Wrong parameter --event_service_AMQP_port (-eAMQP)"
                    help
                    exit 1
                fi
                ;;

            -eGUI | --event_service_GUI_port )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]]; then
                    event_service_GUI_port=$1
                else
                    error "Wrong parameter --event_service_GUI_port (-eGUI)"
                    help
                    exit 1
                fi
                ;;

            -db_host | --database_host )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]]; then
                    database_host=$1
                else
                    error "Wrong parameter --database_host (-db_host)"
                    help
                    exit 1
                fi
                ;;

            -db_port | --database_port )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]]; then
                    database_port=$1
                else
                    error "Wrong parameter --database_port (-db_port)"
                    help
                    exit 1
                fi
                ;;

            -db_name | --database_name )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]]; then
                    database_name=$1
                else
                    error "Wrong parameter --database_name (-db_name)"
                    help
                    exit 1
                fi
                ;;

            -db_user | --database_user )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]]; then
                    database_user=$1
                else
                    error "Wrong parameter --database_user (-db_user)"
                    help
                    exit 1
                fi
                ;;

            -db_pass | --database_pass )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]]; then
                    database_pass=$1
                else
                    error "Wrong parameter --database_pass (-db_pass)"
                    help
                    exit 1
                fi
                ;;

            -w | --workers )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]]; then
                    N_workers=$1
                else
                    error "Wrong parameter --workers (-w)"
                    help
                    exit 1
                fi
                if ! [[ "$N_workers" =~ ^[0-9]+$ ]]; then
                    error "Wrong number of workers"
                    help
                    exit 1
                fi
                ;;


            -db | --database )
                shift
                if [[ "${command}" == "clean_database" ]]; then
                    database=$1
                else
                    error "Wrong parameter --database (-db)"
                    help
                    exit 1
                fi
                ;;

            -k8s_d_n | --k8s_docker_hub_name )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]] && [[ "${mode}" == "k8s" ]]; then
                    k8s_docker_hub_name=$1
                else
                    error "Wrong parameter --k8s_docker_hub_name"
                    help
                    exit 1
                fi
                ;;

            -k8s_d_p | --k8s_docker_hub_port )
                shift
                if [[ "${command}" == "up" ]] || [[ "${command}" == "restart" ]] && [[ "${mode}" == "k8s" ]]; then
                    k8s_docker_hub_port=$1
                else
                    error "Wrong parameter --k8s_docker_hub_name"
                    help
                    exit 1
                fi
                ;;

            -s | --services )
                shift
                services=()
                i=0
                while [[ "$1" != "" ]]; do
                    services[$i]=$1
                    i=${i}+1
                    shift
                done
                ;;

            * )
                help
                exit 1
        esac
        shift
    done
    dependency_check
fi

${command}
