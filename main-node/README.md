## Main node.

Also, you could just pull the image `docker pull semendiak/benchmark_squeezing_remote_serv:1.2` and change the Worker Service address configuration inside the docker.

### Included logic:
* Reading task description (from **task.json**) and task data (**taskData.json**)
* Picking uniformly random distributed points from this dataset (made by Sobol in **main.py**).
* Performing measurements for this data points using Worker Service (**WorkerService.py**)
* Building regression model for data points that was measured (**regression.py**), if model was not built - measure one more point.
* Predicting point with minimum energy (in **regression.py**) and evaluating this (in **main.py**). 