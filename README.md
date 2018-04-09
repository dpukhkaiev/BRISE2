# benchmark
The basic architecture for testing approaches to reducing a benchmarking costs

###### TODO : Start a cluster. Launch the API, Master, a Proxy and DNS discovery

```bash
$ docker-compose up -d         # start containers in background
$ docker-compose kill          # stop containers
$ docker-compose up -d --build # force rebuild of Dockerfiles
$ docker-compose rm            # remove stopped containers
$ docker ps                    # see list of running containers
$ docker exec -ti [NAME] bash  # ssh to the container
$ docker inspect [container_id] # view the output of the application
$ docker logs [container_id] # view details on the state
$ docker-compose restart [service]
```