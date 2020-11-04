# Worker node 

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
3. Find a path to your valid experiment description. For example `"main_node/Resources/GA/GAExperiment.json"`
4. Call the function:
 ```python
 generate_worker_function("main_node/Resources/GA/GAExperiment.json")
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


#### Worker with Genetic algorithm

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

#### Worker for RapidMiner Machine Learning algorithms optimization

By default BRISE is not connected to [RapidMiner](https://rapidminer.com) data science platform. However, a template for using RapidMiner with BRISE is prepared. Please, see this [guide](./RapidMiner_worker_setup_guide.md) to setup BRISE for RapidMiner use case.

#### Worker as Low-Level Meta-heuristic
##### Summary:

BRISE is able to run the optimization tasks by (1) *controlling the configuration* of solver inside of workers 
and/or (2) *selecting the solving* algorithm. In both cases, the selection is guided by intermediate performance 
of system. It defines Reinforcement Learning-based optimization problem-solving process.

More (theoretical) details could be found [here](https://github.com/YevheniiSemendiak/tud_master_benchmarks).

##### Details:
Currently BRISE is able to run low-level meta-heuristics, implemented in two frameworks: 
python-based [jMetalPy](https://github.com/jMetal/jMetalPy) and java-based [jMetal](https://github.com/jMetal/jMetalPy).

To define the respective experiment description file, one should define the respective search space description and experiment description file.
The search space description should contain a set of choices for solver as `low level heuristic` root categorical parameter.
The parameter choices should be defined as the respective children's parameters. 

The examples of experiment description files may be found at [main_node/Resources/HyperHeuristic](../main_node/Resources/HyperHeuristic) folder.

##### Some tips for setting-up BRISE:
1. Disable Repeater by setting it type to `QuantityBased` and setting its parameter `MaxTasksPerConfiguration` equal to 1.
2. Set task execution time (budget) equal to approximately 10% of overall running time (if time-based BRISE stop condition is used). 

##### The workflow of task execution in workers for this use-case is following:
1. Task arrives to worker node and the respective worker method is executed in order to run low-level heuristic (worker.py#tsp_hh method).
2. [LLH Runner](worker_tools/hh/llh_runner.py) is instantiated with respective LLH wrapper 
(jMetalPy MHs are ran with help of [JMetalPyWrapper](worker_tools/hh/llh_wrapper_jmetalpy.py), 
while jMetal Evolution Strategy (currently only one MH could be used from jMetal framework) execution is controlled by [JMetalWrapper](worker_tools/hh/llh_wrapper_jmetal.py))
3. Wrapper constructs the requested LLH with provided parameters, 
attaches the available solution for current optimization problem, 
executes the LLH and reports the results, including the newly obtained solutions. 
Please note, some execution steps in JMetalPy wrapper are cached to reduce the computation effort.
4. THe results are forwarded by Runner to the main-node.

###### Please note, to provide all required functional requirements, both frameworks were slightly modified. Modified code could be found [here](https://github.com/YevheniiSemendiak/jMetalPy/tree/apsp) and [here](https://github.com/YevheniiSemendiak/jMetal/tree/feature/warm_starup_brute_impl).
