# Transfer learning
Transfer learning (TL) is an optional feature of BRISE which is aimed at improving optimization results using knowledge gained in previous experiments. It may be enabled or disabled in settings:
 ```json
   "TransferLearning":{
    "isEnabled": true
   }
 ```

General transfer learning process consists of two main stages:
1. Finding the most similar ones among previous experiments (i.e., identifying transfer expediency for the source experiments)
2. Extracting and applying knowledge to a new (target) experiment

 ## Transfer expediency determination
The functionality of the first step is covered by the `transfer_expediency` module. `transfer_expediency_analyser` uses one of the available comparators to define the most similar experiments among all source experiments.

Currently available comparators are:
- Norm-Difference comparator
- RGPE-based comparator

 ### Norm-Difference comparator
Within this approach, the relatednes between the source and the target experiments is defined by the norm of their difference function based on the metric proposed in: https://link.springer.com/chapter/10.1007/978-3-319-97304-3_4

 ### RGPE-based comparator
This comparator computes ranking loss for each sample from the posterior over target points, based on the rank-weighted Gaussian process ensemble (RGPE) method [Feurer, Letham, Bakshy ICML 2018 AutoML Workshop] Original paper: https://arxiv.org/pdf/1802.02219.pdf

This module can be extended with new custom comparators that match the structure of the Abstrаct comparator. Abstract Comparator contains a Template-method `get_similar_experiments()` with the following steps:
        1. Get source and target labels
        2. Compute similarity metric
        3. Get number of similar experiments (using clustering, static number, etc.)
Clustering algorithms expose another variability point of this module. By default, the Mean Shift clustering algorithm is used: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.MeanShift.html 

Transfer expediency determination may be configured as follows: 
- `ComparatorType` defined, which comparator should be used; 
- `MinNumberOfSamples` allows to tune the quality of expediency determination. The more similar samples in two experiments, the more similar the experiments. However, if this number is too large, it becomes more difficult to find at least one similar instance;
- `NumberOfSimilarExperiments` you can specify the desired number of the most similar experiments to extract knowledge from (e.g., you would like to take only one, the most similar experiment). Alternatively, you can apply clustering to determine the optimal number of such experiments for a particular case.
- `ClusteringAlgorithm` - if clustering is used, the algorithm can be changed using this parameter.

 ```json
    "TransferExpediencyDetermination": {
      "ComparatorType": "NormDifferenceComparator",
      "MinNumberOfSamples": 10,
      "NumberOfSimilarExperiments": "use_clustering",
      "ClusteringAlgorithm": "MeanShiftClustering"
    }
 ```

 ## Extracting and applying knowledge to a new (target) experiment
There exist a number of approaches to improve the quality of optimization using prior knowledge. BRISE can optionally use the following ones:
1. Multi-surrogate-model recommendation (`model_recommendation` folder)
2. Multi-task learning (`multi_task_learning` folder)

Each of these feature has two modes: `standard` and `few-shot`. `few-shot` is aimed at finding a sub-optimal solution already after a few evaluations. `standard` mode does not have this limitation and can be performed until the desired solution quality is achieved.

 ### Multi-surrogate-model recommendation
The idea behind model recommendation is to analyze the performance of various combinations of surrogates in previous runs of the experiment and recommend the best one for use in a target experiment. In its `standard` mode, only model types are recommended, but the surrogates themselves are re-created based on the data available in target experiment. In `few-shot` mode, instances of the built models are injected directly into the target experiment in order to make a prediction of a good configuration based on old information about the search space.

 ```json
    "ModelsRecommendation": {
      "DynamicModelsRecommendation":{
        "RecommendationGranularity": 15,
        "COMMENT": "Min: 1 (recommend every iteration). Max: inf (recommendation for the whole experiment)",
        "TimeToBuildModelThreshold": 0.21,
        "TimeUnit": "seconds",
        "ThresholdType": "soft"
      },
      "FewShot": {}
    }
 ```
 `RecommendationGranularity` - this parameter indicates how often the mechanism of choosing an appropriate model (or rather
models’ combination) should be triggered.
 `TimeToBuildModelThreshold` allows you to specify the maximum allowable time threshold for building a surrogate model, if it is relevant for your experiment.
 `ThresholdType` allows to trade-off an importance of the time criterion, varying the type of a threshold. If the `soft` threshold is chosen, the focus is shifted to the performance criterion, and a “slow” models’ combination may still be used if its performance is better than the average one. In the case of a `hard` threshold type, any violation of the time threshold is prohibited.
 `FewShot` mode does not have any additional parameters. However, if this mode is used, it makes sense to use the few-shot learning-based stop condition, which stops an experiment as soon as the few-shot technique was applied and the knowledge was transferred (see `main_node/stop_condition/few_shot_learning_based.py`).

 ### Multi-task learning
 Unlike `model_recommendation`, in `multi_task_learning`, useful knowledge is represented by configurations, not surrogates. In its `standard` mode, `multi_task_learning` enriches knowledge about the search space by inserting configurations and their labels (corresponding values of the objective function) into the model. In `few-shot` mode, the model is given knowledge of only one best configuration so that it can evaluate it in a target experiment: If the search space of the source and target experiments are similar, the result should be good in the new experiment as well.

 ```json
 "MultiTaskLearning": {
      "Standard":{
        "OldNewConfigsRatio" : 2.416424349152367,
        "COMMENT": "coefficient multiplied by the number of measured configurations in current experiment",
        "TransferBestConfigsOnly": true,
        "TransferFromMostSimilarExperimentsFirst": false
      },
      "FewShot": {}
    }
 ```
 `OldNewConfigsRatio` determines what ratio should be maintained between the old configurations transferred from the source experiment and the new ones.
 `TransferBestConfigsOnly` determines whether only configurations with good objective function values or random configurations should be injected into the target surrogate.
 `TransferFromMostSimilarExperimentsFirst` - it may happen that the `transfer_expediency` module returned a significant number of similar experiments, knowledge of which can be used for the target one. However, since each of the source experiments may contain thousands of configurations, it may be advisable to focus only on the most similar experiment(s) and its configurations.

`transfer_learning_module.py` plays the role of an orchestrator for the whole TL functionality.

More information about the mentioned transfer learning methods, their parameters and effectiveness can be found in: https://nbn-resolving.org/urn:nbn:de:bsz:14-qucosa2-733135
