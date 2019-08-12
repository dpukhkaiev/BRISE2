# BRISE 2.2.0
##### Benchmark Reduction via Adaptive Instance Selection
Software Product Line for Parameter Tuning\
Initial use case: search of an optimal sweet-spot configuration (`CPU Frequency` and `number of threads`) for 
different algorithms (data compressing, integers sorting, etc.) w.r.t. `energy consumption minimization` 
(optimization goal).  

## Getting started
#### Requirements
Software requirements:
- Docker (with Docker Engine 18.06.0+), Docker-compose (1.22.0+).
- Python (v3.7+).

Hardware requirements:
- 5 GB HDD, 2 GB RAM, 2x 2.5 GHz CPU + Resources for running  `N` (amount of workers, 3 by default) instances of your system.

#### Installing and running basic installation
To get working instance of BRISE:
- `git clone` this repository and
- `docker-compose up --build` BRISE instance in root folder of copied repository.

This will create following docker containers:
- [main-node](./main-node/README.md "Main node Readme.") - for exploring of configuration search space, 
deciding which configuration should be evaluated (using Worker Service), 
predicting and validating best configuration.
- [worker-service](./worker_service/README.md "Worker service Readme.") - for parallelization and orchestration of configuration evaluation between worker nodes.
- `N` [workers](./worker/README.md) - for evaluation of your system with concrete parameters.
- [front-end](./front-end/README.md) - for controlling and visualisation of the Experiment process.

#### Testing installation
- Get into **main-node**:
    - `$ docker exec -it main-node /bin/bash`
    - Run BRISE by `python3.7 main.py` inside container. In the end you will see final report for Energy Experiment. (Searching for best CPU Frequency and number of Threads.)

## Using BRISE 
To apply this BRISE for your system, you need to:
1. Install BRISE.
2. Describe Experiment for finding the Configuration for your system in `*.json` [Experiment Description file](./main-node/Resources/EnergyExperiment.json "Example of task description for energy consumption").
3. Describe search space of all possible parameters in `*.json` [Experiment data file](./main-node/Resources/EnergyExperimentData.json "Example for energy consumption - possible CPU frequencies and number of thread").
*These files should be inside main-node container (put it in main-node folder).*
4. Adapt BRISE system to your particular optimization goal (if needed).
Mostly it should be done in validation of predicted configurations by BRISE model (model validation).
5. Launch BRISE and check the results.

## Dev instructions. Local environment 
#### Main-node
Main node have single entry point - **main.py** in a root of main-node folder, so you could easily run it locally,
after satisfying needed requirements.   

See **main-node** requirements in corresponding [requirements.txt](./main-node/requirements.txt) file.

#### Front-end
There is already built version at the start of containers. Just go to [localhost](http://localhost/).

If require to make own front-end build:
1. Install Node.js version 6.9+
2. Update NPM to version 3.0+
3. `$ npm install @angular/cli -g`
4. From front-end root `$ npm install`
5. Start front-server with `$ ng serve --host 0.0.0.0 --port 80`
6. Go to [localhost:80](http://localhost:80)

## Questions, contributing.
##### Questions, suggestions, remarks? Feel free to contact us via [:mailbox_with_mail:](mailto:dmytro.pukhkaiev@tu-dresden.de)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
>>>>>>> /tmp/meld-tmp-Remotevpqarmh6
