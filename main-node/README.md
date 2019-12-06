## Main node.
###### This folder contains main BRISE logic for parameter balancing.

#### Dependencies

- Python 3.7,
- Python external modules listed in [requirements](./requirements.txt)
- [Worker Service](../worker_service/README.md "Part of this project, performs task distribution and running. See worker_service readme for more details.")


#### How to run

Entry point is the `main.py` module.

There is also a wrapper for the main.py, that contains Websocket and HTTP server in `api-supreme.py` module.
It exposes HTTP commands to control BRISE launch and run (start, stop, check status and download Experiment dump)
and Websocket server for data fetching (used in front-end and benchmarking nodes).

- Run BRISE with default configuration files ([Experiment Description](Resources/EnergyExperiment.json) and [global configuration](./GlobalConfig.json)):

`python3.7 main.py`

- Run BRISE with specific Experiment Description file:

`python3.7 main.py ./relative/path/to/config/file.json`