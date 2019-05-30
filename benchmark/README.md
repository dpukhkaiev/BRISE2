# Benchmark :chart_with_upwards_trend:
 
A comparative analysis of the experiments. Designed for understanding, interpreting and assessment of the results of the experiments.

  - Main metrics of the experiment. (`table.py`)
  - Improvements for the best result on each iteration of the experiment (`improvements.py`)
  - Statistical distribution for all and average results on each configuration in the experiment. (`box_statistic.py`)
  - Average results and measurement repeats for experiments. Statistical significance and invariability. Effect of the repeater (`repeat_vs_avg.py`)
  - Experiments configurations (`exp_config.py`)

___
### Usage 
##### Structure
- `./results/serialized` default folder for storing dump of experiments. 
- `./results/reports` output folder for report files
- `./plots` code, generating atomic figures and tables
- `./templates` template for the report file, provides slots for the atomic figures.
- `./benchmark.py` entry point. Combines a template with actual figures and generates a report file.
- `./init.sh` provides simplify commands. For more information `./init.sh help`

##### Run
1. Run the experiment.
2. Save experiment dump:
	1. With front-end: After the end of the experiment running use the button "Save experiment" to download the dump. Pass this file to the `./results/serialized` directory.
	2. Without front-end: Use the command `./init.sh extract` from the "benchmark" directory. Dump files will save to the `./results/serialized` by default. For more setting use [`docker cp`](https://docs.docker.com/engine/reference/commandline/cp/).
3. Build and run the benchmark container:
	1. For first run use: `$ ./init.sh up` from the "benchmark" directory.
	2. For rerun you can use: `$ ./init.sh restart` from the "benchmark" directory.
4. Use the browser to open the reports files. Reports files are stored in `./results/reports` directory.
___
### Play Around with Code

Benchmark currently can be extended and modified with the following dependencies. Documentation on how to use them in your own benchmarking are linked below.

| Dependencies | Description |
| ------ | ------ |
| [Plotly](https://plot.ly/python/) | Python graphing library |
| [Jinja2](http://jinja.pocoo.org/docs/2.10/) | Templating language for Python |
| [Docker](https://docs.docker.com/) | Containerization |

### Todos :construction:

 - Write plots for a large number of experiments

