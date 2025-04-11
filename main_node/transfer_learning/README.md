# Transfer learning
Transfer learning (TL) is an optional feature of BRISE which is aimed at improving optimization results using knowledge gained in previous experiments. It may be enabled or disabled in settings:
 ```json
TransferLearning ? {
  TransferExpediencyDetermination {
    ...
  }
  xor ModelRecommendation ? {
    ...
  }
  MultiTaskLearning ? {
    ...
  }
  [self.MultiTaskLearning or self.ModelRecommendation]
}
 ```

General transfer learning process consists of two main stages:
1. Finding the most similar ones among previous experiments (i.e., identifying transfer expediency for the source experiments)
2. Extracting and applying knowledge to a new (target) experiment

 ## Transfer expediency determination (TED)
 ```json
TransferExpediencyDetermination {
    SamplingLandmarkBased {
      MinNumberOfSamples -> integer
      [MinNumberOfSamples >= 1]
      Type -> predefined
      [Type = "sampling_landmark_based"]
      xor Comparator {
        NormDifference {
          Type -> predefined
          [Type = 'norm_difference_comparator']
        }
        RGPE {
          Type -> predefined
          [Type = 'rgpe_comparator']
        }
      }
      xor ExperimentsQuantity {
        FixedQuantity {
          NumberOfSimilarExperiments -> integer
          [NumberOfSimilarExperiments >= 1]
        }
        AdaptiveQuantity {
          xor Clustering {
            MeanShift {
              Type -> predefined
              BandwidthType -> string
              bandwidth -> float
              quantile -> float
              [BandwidthType in {"Fixed", "Estimated"}]
              [if BandwidthType == "Fixed" then bandwidth <= 1]
              [if BandwidthType == "Fixed" then bandwidth >= 0]
              [if BandwidthType == "Fixed" then quantile == -1]
              [if BandwidthType == "Estimated" then bandwidth == -1]
              [if BandwidthType == "Estimated" then quantile <= 1]
              [if BandwidthType == "Estimated" then quantile >= 0]
              [Type = 'mean_shift_clustering']
            }
          }
        }
      }
    }
}
 ```
The functionality of the first step is covered by the [transfer_expediency_determination](transfer_expediency_determination) module.
The only available strategy is a sampling-landmark-based approach, which uses one of two 
available comparators to define the most similar experiments among all source experiments.

Currently available comparators are:
- [Norm-Difference comparator](transfer_expediency_determination/norm_difference_comparator.py)
- [RGPE-based comparator](transfer_expediency_determination/rgpe_comparator.py)

 ### Norm-Difference comparator
Within this approach, the relatedness between the source and the target experiments is defined by the norm of their difference function based on the metric proposed in: https://link.springer.com/chapter/10.1007/978-3-319-97304-3_4

 ### RGPE-based comparator
This comparator computes ranking loss for each sample from the posterior over target points, based on the rank-weighted Gaussian process ensemble (RGPE) method [Feurer, Letham, Bakshy ICML 2018 AutoML Workshop] Original paper: https://arxiv.org/pdf/1802.02219.pdf

SamplingLandmarkBased TED can be extended with new custom comparators that match the structure of the Abstrаct comparator. 
Abstract Comparator contains a Template-method `get_similar_experiments()` with the following steps:
        1. Get source and target labels
        2. Compute similarity metric
        3. Get number of similar experiments, using a fixed value from the user (`FixedQuantity`) or determining the number adaptively (`AdaptiveQuantity`).

Adaptive strategy assumes utilization of a clustering algorithm among which the [Mean Shift clustering](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.MeanShift.html) algorithm is available.

 ## Extracting and applying knowledge to a new (target) experiment
There exist a number of approaches to improve the quality of optimization using prior knowledge. BRISE can optionally use the following ones:
1. [Multi-surrogate-model recommendation](model_recommendation)
2. [Multi-task learning](multi_task_learning)

Each of these feature has two modes: `Standard` and `FewShot`. `FewShot` is aimed at finding a near-optimal solution already after several evaluations. 
`Standard` mode does not have this limitation and can be performed until the desired solution quality is achieved.
 ### Multi-surrogate-model recommendation (MR)
 ```json
xor ModelRecommendation ? {
    DynamicModelsRecommendation {
      xor RecommendationGranularity {
        Finite {
          Value -> integer
          [Value >= 1]
        }
        Infinite {
          Value -> predefined
          [Value = "inf"]
        }
      }
      xor PerformanceMetric {
        AverageRelativeImprovement {
          Type -> predefined
          [Type = 'average_relative_improvement']
        }
      }
      Type -> predefined
      ThresholdType -> string
      TimeToBuildModelThreshold -> float
      TimeUnit -> string

      [ThresholdType in {"Hard", "Soft"}]
      [TimeUnit in {"seconds", "minutes", "hours", "days"}]
      [TimeToBuildModelThreshold > 0]
      [Type = 'dynamic_model_recommendation']
    }
    FewShotRecommendation {
      Type -> predefined
      [Type = 'few_shot']
      [fcard.StopCondition.Instance.FewShotLearningBasedSC = "+"]
      [self excludes TransferLearning.MultiTaskLearning.Filters.FewShotMultiTask]
    }
}
 ```
The idea behind model recommendation is to analyze the performance of various combinations of surrogates in previous 
runs of the experiment and recommend the best one for use in a target experiment. 
In its `Standard` mode, only model types are recommended, but the surrogates themselves are re-created based on the 
data available in target experiment. In `FewShot` mode, instances of the built models are injected directly into 
the target experiment in order to make a prediction of a good configuration based on old information about the search space.

 `RecommendationGranularity` - this feature indicates how often the mechanism of choosing an appropriate model (or rather
models’ combination) should be triggered.
 `TimeToBuildModelThreshold` allows you to specify the maximum allowable time threshold for building a surrogate model, 
 if it is relevant for your experiment.
 `ThresholdType` allows to change importance of the time criterion, varying the type of the threshold. 
 If `Soft` threshold is chosen, the focus is shifted to the performance criterion, and a “slow” models’ 
 combination may still be used if its performance is better than the average one. In case of a `Hard` 
 threshold, any violation of the time threshold is prohibited.
 `FewShot` mode does not have any additional parameters. However, if this mode is used, 
 the model makes sure that the few-shot learning-based stop condition is available, which stops an experiment as soon 
 as the few-shot technique was applied and the knowledge was transferred (see [here](../stop_condition/few_shot_learning_based.py)).

 ### Multi-task learning (MTL)
 ```json
MultiTaskLearning ? {
    or Filters {
      OldNewRatio{
        Type -> predefined
        [Type = 'old_new_ratio']
        OldNewConfigsRatio -> float
        [OldNewConfigsRatio > 0]
      }
      FewShotMultiTask {
        Type -> predefined
        [Type = 'few_shot']
        [fcard.StopCondition.Instance.FewShotLearningBasedSC = "+"]
      }
      OnlyBestConfigurations  {
        Type -> predefined
        [Type = 'only_best']
      }
      ShuffleConfigurations {
        Type -> predefined
        [Type = 'shuffle']
      }
    }
```
The general workflow of multi-task learning is straightforward. 
First, from all source experiments which were provided by TED module, it extracts all configurations and their 
respective objective function values.  
Then, one or several filters are applied to the extracted configurations in order to adapt the list of transferred 
configurations according to the needs of the experiment designer. 
* `OldNewRatio` determines the number of transferred configurations in comparison to the number of newly measured configurations.
In case this number is smaller than the number of all source configurations, MTL start with the most similar source experiment.
* 	To support handling of very expensive problems, we offer a `FewShotMultiTask` Filter, which returns only the best configuration from the most similar source experiment.
* `OnlyBestConfigurations` filter transfers only configurations whose values are better than the average. By this, we try to shift the subsequent optimization process to a more promising area.
* `ShuffleConfigurations` filter randomizes configurations to be transferred by selecting them from random source experiments. Here, our intention is to increase exploration of the subsequent optimization process.
 

