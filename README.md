# :carousel_horse: Benchmark 
###### Early BETA
> The architecture for testing approaches to reducing a benchmarking costs

### Basic info
The objective of this progect is to reduce the amount of effort spent on benchmarking, whilst minimizing the deterioration of result’s quality compared to a full benchmarking process.

***

## Components
### Back End
- [Main thread](./main-node) regresion, experiment selection, assumption
- [Worker service](./worker_service) experiment managing, encapsulation, result storing 
- [Worker](./worker_node) experiment execution

### Front-end
- [Front-and](./front-end) monitoring the experiments
___
#### Dev instructions. Local environment :computer:
###### Front-end
1. Install Node.js version 6.9+
2. Update NPM to version 3.0+
3. `$ npm install @angular/cli -g`
4. From front-end root `$ npm install`
5. Start front-server with `$ ng serve --host 0.0.0.0 --port 4201`

###### Back-end + Docker environment + Main thread
1. Install Docker and docker-compose
2. Verify worker-node ip address and change it in **main-node/GlobalConfig.json** (you may do it later).
3. `$ docker-compose up -d --build`

###### Main thread
1. SSH into container: `ssh root@localhost -p 2222` (password is "root" or you could add you public key to **configure_sshd.sh** file) 
* Run main script: `./main.sh`

### Technologies stack :wrench:
- Front-end | [Angular-cli](https://cli.angular.io/ "Angular CLI"), [Angular material](https://material.angular.io/ "Angular material")
- Worker + Worker service | Python 3.6, [Flask](http://flask.pocoo.org/docs/0.12/ "Flask"), [Requests](http://docs.python-requests.org/en/master/ "Requests")
- Main thread | Python 3.6, [scikit-learn](http://scikit-learn.org/stable/ "Scikit-learn")

___

##### Have questions, proposes? Fill free to contact us via :mailbox_with_mail: 
