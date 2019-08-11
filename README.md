# BRISE 2.0.0
##### Benchmark Reduction via Adaptive Instance Selection
Hyperparameter optimization framework.\
Initial use case: search of an optimal sweet-spot configuration (`CPU Frequency` and `number of threads`) for 
different algorithms (data compressing, integers sorting, etc.) w.r.t. `energy consumption minimization` 
(optimization goal).  

## Getting started
#### Requirements
Software requirements:
- Docker (with Docker Engine 18.06.0+), Docker-compose (1.22.0+).
- Python3.

Hardware requirements:
- 5 GB HDD, 2 GB RAM, 2x 2.5 GHz CPU + Resources for running  `N` (Equal to number of workers. 3 by default) instances of your system.

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

#### Testing installation
- Get into **main-node**:
   - If BRISE running locally:\
    `$ docker exec -it main-node /bin/bash`
   - If BRISE running remotely - use [openssh server](./main-node/configure_sshd.sh "Configuration of ssh server, adapt it for your requirements!") running inside main node:\
    `$ ssh root@IP_ADDR -p 2222` \
    By default, exposed ssh port **from** container is *2222*. Password is "root". You could also add you public key to **configure_sshd.sh** file.
- Run BRISE by `python3 main.py` inside container. In the end you will see final report for default task. (Searching for best CPU Frequency and number of Threads.)  

## Using BRISE 
To apply this BRISE for your system, you need to:
1. Install BRISE.
2. Describe task of finding configuration for your system in `*.json` [configuration file](./main-node/Resources/task.json "Example of task description for energy consumption"). 
3. Describe search space of possible configurations in `*.json` [file](./main-node/Resources/taskData.json "Example for energy consumption - possible CPU frequencies and number of thread"). 
*This files should be inside main-node container (put it in main-node folder).* 
4. Adapt BRISE system to your optimization goal. 
Mostly it should be done in validation of predicted configurations by BRISE.
5. Run BRISE and see results.   

## Dev instructions. Local environment 
#### Main-node
> During integration BRISE to your system you should adapt **main node** to your system. 
Main node have single entry point - **main.py** in a root of main-node folder, so you could easily run it locally,
after satisfying needed requirements.   

See requirements for running **main-node** logic locally [here](./main-node#dependencies).

#### Front-end
There is already built version at the start of containers. Just go to [localhost](http://localhost/).

If require to make own front-end build:
1. Install Node.js version 6.9+
2. Update NPM to version 3.0+
3. `$ npm install @angular/cli -g`
4. From front-end root `$ npm install`
5. Start front-server with `$ ng serve --host 0.0.0.0 --port 4201`
6. Go to [localhost:4201](http://localhost:4201)

## Questions, contributing.
##### Questions, suggestions, remarks? Feel free to contact us via [:mailbox_with_mail:](mailto:dmytro.pukhkaiev@tu-dresden.de)

## Authors
- **[Dmytro Pukhkaiev](https://github.com/dpukhkaiev)** - *[initial idea](https://doi.org/10.1145/3194078.3194082)*, [initial version of BRISE](https://github.com/dpukhkaiev/BRISE).
- **[Oleksandr Husak](https://github.com/Valavanca/)** - Worker service and workers, front-end developing.
- **[Ievgeniia Svetsynska](https://github.com/IevgSvet)** - Front-end APIs, improvements.
- **[Roman Kosonvnenko](https://github.com/pariom)** - Applying BRISE to different systems, improvements.
- **[Yevhenii Semendiak](https://github.com/YevheniiSemendiak)** - main node logic.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
