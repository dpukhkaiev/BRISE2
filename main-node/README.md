## Main node.
###### This folder contains main BRISE logic for parameter balancing.


#### Dependencies 
###### All dependencies will be installed during docker container building, for full list check [main node dockerfile](./Dockerfile).
- Python 3.6, 
- Python modules: 
    - [NumPy](www.numpy.org)
    - [SciPy](https://www.scipy.org/)
    - [Scikit-learn](http://scikit-learn.org/)
    - [Flask](http://flask.pocoo.org/docs/0.12/ "Flask")
    - [Requests](http://docs.python-requests.org/en/master/ "Requests")
    - [Python-sockerio](https://pypi.org/project/python-socketio/)
    - [Eventlen](https://pypi.org/project/eventlet/)
- [Worker Service](../worker_service/README.md "Part of this project, performs task distribution and running. See worker_service readme for more details.")


#### How to run 
Entry point - main.py Python 3 file.

- Run BRISE with default configuration files ([task configuration](./Resources/task.json) and [global configuration](./GlobalConfig.json)):

`python3 main.py` 

- Run BRISE with specific task configuration file:

`python3 main.py ./relative/path/to/config/file.json`
