## Main node.


### How to run
* Clone this repository and enter this folder.
* Verify worker-node ip address and change it in **GlobalConfig.json** (you may do it later).
* Run `docker build .` to build image 
* Run container from built image exposing port 2222 for ssh: `docker run -p "2222:2222" -d IMAGE_ID`
* SSH into container: `ssh root@localhost -p 2222` (password:root or you could add you public key to **configure_sshd.sh** file) 
* Run main script: `python3 main.py`

Also, you could just pull the image `docker pull semendiak/benchmark_squeezing_remote_serv:1.2` and change the Worker Service address configuration inside the docker.

### Included logic:
* Reading task description (from **task.json**) and task data (**taskData.json**)
* Picking uniformly random distributed points from this dataset (made by Sobol in **main.py**).
* Performing measurements for this data points using Worker Service (**WorkerService.py**)
* Building regression model for data points that was measured (**regression.py**), if model was not built - measure one more point.
* Predicting point with minimum energy (in **regression.py**) and evaluating this (in **main.py**). 