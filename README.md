# BRISE 2.6.0
##### Benchmark Reduction via Adaptive Instance Selection
![BRISE-CI](https://github.com/dpukhkaiev/BRISE2/workflows/BRISE-CI/badge.svg?branch=master)

A Software Product Line for Parameter Tuning 

## Getting started
#### Requirements
- Docker (with Docker Engine 27.5.1+), Docker-compose (2.32.4+).
- Python (v3.12+).
- [jq](https://stedolan.github.io/jq/) (v1.6+)
- Kubectl (v1.18.0+) only in case of using Kubernetes.

#### Installing and running basic installation
To get a working instance of BRISE:
- `git clone` this repository and
- `./brise.sh up -m docker-compose` in the root folder of copied repository to deploy the BRISE instance using *docker-compose*.

Run  `./brise.sh help` to see possible options for starting it. For example, if you want to overwrite the standard addresses and ports used by the `event-service` or `database`, you may use the following command:
`./brise.sh up -m docker-compose -eAMQP 49153  -eGUI 49154 -db_host localhost -db_port 27017`
If no values are specified, the default ones will be taken from the [deployment file](./deployment_settings/LocalDeployment.json).

`NOTE. brise.sh is designed for UNIX operating system. Running the script under Windows Subsystem for Linux may 
require additional actions, for example, using [dos2unix](https://linux.die.net/man/1/dos2unix) tools.` 

The following Docker containers will be created:
- [main-node](./main_node/README.md "Main node Readme.") - performs the main flow of an optimization experiment. Contains 
extensible features to customize your optimization process.
- ~~[worker-service](./worker_service/README.md "Worker service Readme.") - parallelization and orchestration of configurations
 between worker nodes.~~ In BRISE v2.6.0 is deprecated.
- `N` [workers](./worker/README.md) - evaluate the target system with concrete parameters.
- ~~[front-end](./front_end/README.md) - control and visualisation of the optimization process.~~ In BRISE v2.6.0 is deprecated.
- [event-service](./event_service/README.md) - [RabbitMQ](https://www.rabbitmq.com/) server instance for event management.
- [mongo-db](./mongo_db/README.md) - [MongoDB](https://www.mongodb.com/) server instance for the BRISE database management.

#### Testing the installation
- Get into **main-node**:
    - `$ docker exec -it main-node /bin/bash`
    - Activate conda environment `conda activate brise-260`
    - Run BRISE by `python3.12 main.py` inside the container. In the end you will see a final report for Radixsort 
    Energy Experiment (search for the best CPU frequency and number of threads of the Radixsort sorting 500 millions of 
     integers w.r.t. energy consumption)

## Using BRISE
To apply BRISE for your target system, you will need to:
1. Install BRISE.
2. Model search space of your experiment within Waffle feature model. 
[Base model](main_node/Resources/tests/waffle_models/base.wfl) can be used as a staring point
3. Launch BRISE and configure your product instance with Waffle frontend [localhost:8000](http://localhost:8000).
*The resulting file must be present in the main-node container (put it into `main_node/Resources/` folder).*
4. Run main script from the `main-node` BRISE referencing your product instance configuration file and check the results.

## Dev instructions. Local environment 
#### Main-node
Main node has a single entry point - **main.py** in a root of the main-node folder, so you can run it locally,
after satisfying needed requirements.   

See **main-node** requirements in a corresponding [environment.yml](./main_node/environment.yml) file and 
[deployment settings](deployment_settings/LocalDeployment.json) for network settings.

#### ~~Front-end~~ In BRISE v2.6.0 is deprecated. Will be returned in the later releases.
There is an already built version running in the front-end container. Just go to [localhost](http://localhost/).

If you would like to make own front-end build:
1. Install Node.js version 6.9+
2. Update NPM to version 3.0+
3. `$ npm install @angular/cli -g`
4. From the front_end folder run `$ npm install`
5. Start front-server with `$ ng serve --host 0.0.0.0 --port 80`
6. Go to [localhost:80](http://localhost:80)

## Questions, contributing.
##### Questions, suggestions, remarks? Feel free to contact us via [:mailbox_with_mail:](mailto:dmytro.pukhkaiev@tu-dresden.de)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
