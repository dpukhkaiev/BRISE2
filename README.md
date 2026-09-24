# BRISE 2.6.1
##### Benchmark Reduction via Adaptive Instance Selection
![BRISE-CI](https://github.com/dpukhkaiev/BRISE2/workflows/BRISE-CI/badge.svg)
![CodeCoverage](./badge-data/coverage.svg)

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

> **_NOTE:_**  If you use a ARM processor go to `waffle/Dockerfile` and uncomment/comment the respective FROM lines. The default is AMD.

`NOTE. brise.sh is designed for UNIX operating system. Running the script under Windows Subsystem for Linux may 
require additional actions, for example, using [dos2unix](https://linux.die.net/man/1/dos2unix) tools.` 

The following Docker containers will be created:
- [main-node](./main_node/README.md "Main node Readme.") - performs the main flow of an optimization experiment. Contains 
extensible features to customize your optimization process.
- ~~[worker-service](./worker_service/README.md "Worker service Readme.") - parallelization and orchestration of configurations
 between worker nodes.~~ In BRISE v2.6.0 is deprecated.
- `N` [workers](./worker/README.md) - evaluate the target system with concrete parameters.
- [front-end](./frontend/README.md) - Vue 3 dashboard for control and visualisation of the optimization process.
- [searchspace-editor](./searchspace_editor/README.md) - visual canvas editor for authoring the `SearchSpace` part of the context model.
- [waffle](./waffle/README.md) - configuration wizard that turns a Waffle feature model into the product configuration JSON `main-node` consumes.
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
[Base model](main_node/Resources/tests/waffle_models/base.wfl) can be used as a staring point.
*The `SearchSpace` part of this model can optionally be designed visually with the
[searchspace-editor](./searchspace_editor/README.md) [localhost:3001](http://localhost:3001) and manually merged
into your model.*
3. Launch BRISE and configure your product instance with Waffle frontend [localhost:8000](http://localhost:8000).
*The resulting file must be present in the main-node container (put it into `main_node/Resources/` folder).*
4. Run main script from the `main-node` BRISE referencing your product instance configuration file and check the results.

## Dev instructions. Local environment 
#### Main-node
Main node has a single entry point - **main.py** in a root of the main-node folder, so you can run it locally,
after satisfying needed requirements.   

See **main-node** requirements in a corresponding [environment.yml](./main_node/environment.yml) file and 
[deployment settings](deployment_settings/LocalDeployment.json) for network settings.

#### Front-end
See [Getting Started](./frontend/README.md#getting-started-local-dev-without-docker) in `frontend/README.md`.

#### Searchspace Editor
See [Getting Started](./searchspace_editor/README.md#getting-started-local-dev) in `searchspace_editor/README.md`.

## Questions, contributing.
##### Questions, suggestions, remarks? Feel free to contact us via [:mailbox_with_mail:](mailto:dmytro.pukhkaiev@tu-dresden.de)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
