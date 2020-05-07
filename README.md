# BRISE 2.4.0
##### Benchmark Reduction via Adaptive Instance Selection
![BRISE-CI](https://github.com/dpukhkaiev/BRISEv2/workflows/BRISE-CI/badge.svg?branch=dev)

Software Product Line for Parameter Tuning\
Initial use case: search of an optimal sweet-spot configuration (`CPU Frequency` and `number of threads`) for 
different algorithms (data compressing, integers sorting, etc.) w.r.t. `energy consumption minimization` 
(optimization goal).  

## Getting started
#### Requirements
Software requirements:
- Docker (with Docker Engine 18.06.0+), Docker-compose (1.22.0+).
- Python (v3.7+).
- [jq](https://stedolan.github.io/jq/) (v1.5-1+)
- Kubectl (v1.18.0+) only in case of using Kubernetes.


Hardware requirements:
- 5 GB HDD, 2 GB RAM, 2x 2.5 GHz CPU + Resources for running  `N` (amount of workers, 3 by default) instances of your system.

#### Installing and running basic installation
To get a working instance of BRISE:
- `git clone` this repository and
- `./brise.sh up -m docker-compose` in the root folder of copied repository to deploy the BRISE instance using *docker-compose*.

Run  `./brise.sh help` to see possible options for starting it. For example, if you want to overwrite the standard addresses and ports used by the `event-service` or `database`, you may use the following command:
`./brise.sh up -m docker-compose -eAMQP 49153  -eGUI 49154 -db_host localhost -db_port 27017`
If no values are specified, the default ones will be taken from the [SettingsBRISE.json](./main-node/Resources/SettingsBRISE.json).

`NOTE. brise.sh is designed for UNIX operating system. Running the script under Windows Subsystem for Linux may 
require additional actions, for example, using [dos2unix](https://linux.die.net/man/1/dos2unix) tools.` 

The following Docker containers will be created:
- [main-node](./main-node/README.md "Main node Readme.") - performs the main flow of an optimization experiment. Contains 
extendable features to customize your optimization process.
- [worker-service](./worker_service/README.md "Worker service Readme.") - parallelization and orchestration of configurations
 between worker nodes.
- `N` [workers](./worker/README.md) - evaluate the target system with concrete parameters.
- [front-end](./front-end/README.md) - control and visualisation of the optimization process.
- [event-service](./event_service/README.md) - [RabbitMQ](https://www.rabbitmq.com/) server instance for event management.
- [mongo-db](./mongo-db/README.md) - [MongoDB](https://www.mongodb.com/) server instance for the BRISE database management.

#### Testing the installation
- Get into **main-node**:
    - `$ docker exec -it main-node /bin/bash`
    - Run BRISE by `python3.7 main.py` inside the container. In the end you will see a final report for Radixsort 
    Energy Experiment (search for the best CPU frequency and number of threads of the Radixsort sorting 500 millions of 
     integers w.r.t. energy consumption)

## Using BRISE 
To apply BRISE for your target system, you will need to:
1. Install BRISE.
2. Describe your experiment in `*.json` 
[Experiment Description file](./main-node/Resources/EnergyExperiment.json "Example of task description for the Energy Experiment").
3. Describe your search space in `*.json` 
[Experiment data file](./main-node/Resources/EnergyExperimentData.json "Example for the Energy Experiment").
*These files should be inside of the main-node container (put it into `main-node/Resources/` folder).*
4. Adapt BRISE to your particular optimization case (if needed) in [SettingsBRISE file](./main-node/Resources/SettingsBRISE.json).
5. Launch BRISE and check the results.

## Dev instructions. Local environment 
#### Main-node
Main node have a single entry point - **main.py** in a root of the main-node folder, so you could easily run it locally,
after satisfying needed requirements.   

See **main-node** requirements in a corresponding [requirements.txt](./main-node/requirements.txt) file.

#### Front-end
There is an already built version running in the front-end container. Just go to [localhost](http://localhost/).

If you would like to make own front-end build:
1. Install Node.js version 6.9+
2. Update NPM to version 3.0+
3. `$ npm install @angular/cli -g`
4. From the front-end folder run `$ npm install`
5. Start front-server with `$ ng serve --host 0.0.0.0 --port 4201`
6. Go to [localhost:4201](http://localhost:4201)

## Questions, contributing.
##### Questions, suggestions, remarks? Feel free to contact us via [:mailbox_with_mail:](mailto:dmytro.pukhkaiev@tu-dresden.de)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
