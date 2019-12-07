### Worker node 

> All code that performs clearing work. The main objective is to reduce staff resources

#### Dependancy
Software requirements:
- Docker
- Python 3.6
- [RabbitMQ service](https://www.rabbitmq.com/)

- [Service](../worker_service/README.md)

#### Get started with a generator tool

By default, worker contains `generator.py` module in the `generator` package. This module contains a function `generate_worker_function` that generates a code **skeleton** of the method that later will be spread between workers. It is a method that **worker** will call to perform a **Task** in your **Experiment**.
The function takes a path to an experiment description and appends skeleton of code to `worker/worker.py`.

The main goal of this mechanism is to help you at the beginning to write your own scenario implementation in the worker. 

To use this function follow next steps:

1. Run Python console in the root folder of the project.
2. Import `generate_worker_function`:
```python
from worker.generator.generator import generate_worker_function
```
3. Find a path to your valid experiment description. For example `"main-node/Resources/GA/GAExperiment.json"`
4. Call the function:
 ```python
 generate_worker_function("main-node/Resources/GA/GAExperiment.json")
```
5. Check result, and fill gaps in a generated skeleton.

#### Get started with Genetic solver algorithm for MQUAT2 project

By default worker contains `jastadd-mquat-solver-genetic-2.0.0-SNAPSHOT.jar` file in the `binaries` folder.

To create your own `jar` file follow next steps:

1. Install [gradle](https://gradle.org/).
2. Download [adapted for BRISE MQUAT2 project](https://git-st.inf.tu-dresden.de/mquat/mquat2/tree/Genetic_Kosovnenko).
3. Compile a `jar` file:
   ```ssh
   ./gradlew -b ./mquat2/jastadd-mquat-solver-genetic/build.gradle jar
   ```
4. Copy `jar` file from `mquat2/jastadd-mquat-solver-genetic/build/libs/` to `BRISEv2/worker/binaries/` folder.
5. Check the name of `jar` file, it must be `jastadd-mquat-solver-genetic-2.0.0-SNAPSHOT.jar`.


##### Worker with Genetic algorithm

[worker.py](./worker.py) contains the function `genetic(param, scenario)`, which executes the `GeneticMain.java` 
from Command Prompt using MQUAT binary in `jastadd-mquat-solver-genetic-2.0.0-SNAPSHOT.jar`:
```python
import os
command = ("java -jar binaries/jastadd-mquat-solver-genetic-2.0.0-SNAPSHOT.jar %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s" % (numTopLevelComponents, avgNumImplSubComponents, implSubComponentStdDerivation, avgNumCompSubComponents, compSubComponentStdDerivation, componentDepth, numImplementations, excessComputeResourceRatio, numRequests, numCpus, seed, timeoutValue, timeoutUnit,generations, populationSize,treeMutateOperatorP, treeMutateOperatorP1, treeMutateOperatorP2,treeMutateOperatorP3, Lambda, crossoverRate, mu, tournament))
os.system(command)
```

`generations`, `populationSize`, `treeMutateOperatorP`, `treeMutateOperatorP1`, `treeMutateOperatorP2`, `treeMutateOperatorP3`, `Lambda`, `crossoverRate`, `mu`, `tournament` are parameters of Genetic algorithm for tuning by [**BRISE**](https://github.com/dpukhkaiev/BRISEv2).

`Filename` is name of the file with results.

`numTopLevelComponents`, `avgNumImplSubComponents`, `implSubComponentStdDerivation`, `avgNumCompSubComponents`, `compSubComponentStdDerivation`, `componentDepth`, `numImplementations`, `excessComputeResourceRatio`, `numRequests`, `numCpus`, `seed`, `timeoutValue`, `timeoutUnit` are parameters of scenario


Path to find the `GeneticMain.java`: [mquat2/jastadd-mquat-solver-genetic/src/main/java/de/tudresden/inf/st/mquat/solving/genetic/GeneticMain.java](https://git-st.inf.tu-dresden.de/mquat/mquat2/blob/Genetic_Kosovnenko/jastadd-mquat-solver-genetic/src/main/java/de/tudresden/inf/st/mquat/solving/genetic/GeneticMain.java).

Worker container stores the results of Genetic algorithm in the `results/scenarios/` folder.

Example of result file:
```csv
name,Solved,Obj,Validity,Valid,TimeOut
genetic_NSGA2,5558,34620.200000000004,0,true,false
```

[Link to MQUAT2 project](https://git-st.inf.tu-dresden.de/mquat/mquat2/tree/Genetic_Kosovnenko).

##### Worker for Spark parameters tuning
BRISE can be applied for tuning parameters of the Apache Spark. An example of such tuning is already pre-configured and adds the following components to BRISE:
1. [SparkExperiment.json and SparkExperimentData.json](./main-node/Resources/spark/) - experiment and search space description files
2. spark-service - container with HDP and Apache Spark installed. Toy [workload](./spark_worker/workload.py) is used for Spark  
3. `spark()` [method](./worker/worker.py) - worker method, that measures Spark task with concrete parameters

*time* to run Spark task is considered to be an objective function and [parameters of `spark-submit` command](https://spark.apache.org/docs/latest/configuration.html) are tunable parameters.

When new configuration is emitted by the main node, it is sent to the worker that forms `spark-submit` command using specified parameters (see `spark()` method) and sends this command to the *spark-service* via SSH. For this purpose SSH server is installed on the *spark-service* and *worker* uses open-ssh client.

The following steps are needed to successfully establish SSH connection between nodes: 
1. add a [key pair](./worker/.ssh)* for N worker nodes 
2. add workers' public key to the list of spark service's \emph{authorized_keys}
3. add spark_service to the list of worker's \emph{known_hosts}
4. disable StrictHostKeyChecking to allow automatic connection

These steps are already performed within the provided Spark use case example.

* *please, note, that static key pair is used for all involved workers. It is done for the sake of simplicity but should be carefully used from the security point of view!*
