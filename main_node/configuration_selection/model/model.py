import itertools
import time
import pandas as pd
import logging

from typing import List, Mapping, Tuple, Dict
from core_entities.search_space import Hyperparameter
from core_entities.configuration import Configuration

from configuration_selection.model.surrogate.surrogate_orchestrator import SurrogateOrchestrator
from configuration_selection.model.surrogate.surrogate_abs import Surrogate
from configuration_selection.model.optimizer.optimizer_orchestrator import OptimizerOrchestrator
from configuration_selection.model.optimizer.optimizer_abs import Optimizer
from configuration_selection.model.validator.validator_orchestrator import ValidatorOrchestrator
from configuration_selection.model.candidate_selector.candidate_selector_orchestrator import CandidateSelectorOrchestrator
from configuration_selection.model.surrogate.composite_surrogate import CompositeSurrogate

from reconfiguration.effector import Effector

class Model:
    def __init__(self, model_name:str, model_description: dict, region: Tuple, objectives: Dict):
        self.model_name = model_name
        self.region = region
        self.objectives = objectives

        self.surrogate_orchestrator = SurrogateOrchestrator()

        self._init_model(model_description, vpoint=model_name)

    @Effector.effector("Model") # VP Name definied by vpoint arg!
    def _init_model(self, model_description, vpoint=None, **kwargs):
        self.model_description = model_description
        self.mo_handling_surrogate_type = None
        
        # surrogate and MO handling
        for i in model_description.items():
            if "MultiObjectiveHandling" in i[0]:
                self.mo_handling_surrogate_type = list(i[1]["SurrogateType"])[0]

        surrogate_descriptions = self._get_descriptions(model_description, "Surrogate")
        self.mapping_surrogate_objective: Mapping[Surrogate, Dict] = {}
        self._surrogate_map: Mapping[str, list[Surrogate]] = {}

        if self.mo_handling_surrogate_type == "Compositional":
            # Create a surrogate for each objective function
            i = 0
            for key, value in self.objectives.items():
                self._init_surrogate(surrogate_descriptions[i], region=self.region, objectives={key: value},
                                     vpoint="Surrogate_" + str(i))
                i += 1
        elif self.mo_handling_surrogate_type == "DynamicCompositional" or self.mo_handling_surrogate_type == "Portfolio":
            for i, s in enumerate(surrogate_descriptions):
                self._init_surrogate(s, region=self.region, objectives=self.objectives,
                                        vpoint="Surrogate_" + str(i))

        else:  # Scalar Pure None
            self._init_surrogate(surrogate_descriptions[0], region=self.region, objectives=self.objectives,
                                 vpoint="Surrogate")

        # optimizer
        self.optimizer_orchestrator = OptimizerOrchestrator()
        optimizer_descriptions = self._get_descriptions(model_description, "Optimizer")
        
        self.mapping_optimizer_objective: Mapping[Optimizer, dict] = {}
        self._optimizer_map: Mapping[str, list[Optimizer]] = {}
        
        if self.mo_handling_surrogate_type == "Compositional":
            i = 0
            for key, value in self.objectives.items():
                self._init_optimizer(optimizer_descriptions[i], region=self.region, objectives={key: value},
                                     vpoint="Optimizer_" + str(i))
                i += 1
        else:
            self._init_optimizer(optimizer_descriptions[0], region=self.region, objectives=self.objectives,
                                 vpoint="Optimizer")

        # validator
        self.validator_orchestrator = ValidatorOrchestrator()
        validator_description = model_description["Validator"]
        self._init_validators(validator_description)

        # candidate selector
        self.candidate_selector_orchestrator = CandidateSelectorOrchestrator()
        candidate_selector_description = model_description["CandidateSelector"]
        self._init_candiate_selector(candidate_selector_description)

        # transfer learning
        self.time_to_build = None
        self.created_surrogates_descriptions_and_objectives_and_optimizer_descriptions = []
        self.model_dumps = None

    # Real VP name provided by kwarg vpoint!
    @Effector.effector("Surrogate", identifiers="model_name")
    def _init_surrogate(self, description, region=None, objectives=None, only_on_mo=False, vpoint=None, initial=True):
        created_surrogates = self._surrogate_map.get(vpoint, [])

        # Remove old surrogates/cleanup
        if initial is False:
            for s in created_surrogates:
                if s in self.mapping_surrogate_objective:
                    del self.mapping_surrogate_objective[s]
            
            del self._surrogate_map[vpoint]

        # Handle DynamicCompositional and Portfolio type
        if self.mo_handling_surrogate_type == "DynamicCompositional" or self.mo_handling_surrogate_type == "Portfolio":
            # Create surrogate for each objective function
            for i, o_name in enumerate(self.objectives.keys()):
                obj = {o_name: self.objectives[o_name]}
                s = self.surrogate_orchestrator.get_surrogate(description, region, obj)
                self.__create_surrogate(description, region, vpoint, obj)

                # Create another one (just once) if the surrogate is multiobjective
                if s.multi_objective is True and i == 0:
                    self.__create_surrogate(description, region, vpoint, self.objectives)
                
            return
        
        # Save created surrogate
        self.__create_surrogate(description, region, vpoint, objectives)

    def __create_surrogate(self, description:dict, region:Tuple, vpoint:str, objectives):
        """Add surrogate to `mapping_surrogate_objective` and `_surrogate_map`"""
        surrogate = self.surrogate_orchestrator.get_surrogate(description, region, objectives)
        self._surrogate_map[vpoint] = self._surrogate_map.get(vpoint, []) + [surrogate]
        self.mapping_surrogate_objective[surrogate] = objectives

    # Real VP name provided by kwarg vpoint!
    @Effector.effector("Optimizer", identifiers="model_name")
    def _init_optimizer(self, description, region=None, objectives=None, vpoint=None, initial=True):
        optimizer = self.optimizer_orchestrator.get_optimizer(description, region, objectives)

        # Remove old optimizer
        created_optimizer = self._optimizer_map.get(vpoint, [])
        if initial is False:
            for o in created_optimizer:
                if o in self.mapping_optimizer_objective:
                    del self.mapping_optimizer_objective[o]
                
            del self._optimizer_map[vpoint]

        # Save created optimizer
        self._optimizer_map[vpoint] = self._optimizer_map.get(vpoint, []) + [optimizer]
        
        self.mapping_optimizer_objective[optimizer] = objectives

    @Effector.effector("Validator", identifiers="model_name")
    def _init_validators(self, description:dict):
        self.external_validator = None
        self.internal_validator = None

        for k in description.keys():
            if k == 'ExternalValidator':
                self.external_validator = self.validator_orchestrator.get_validator(description[k], self.region, self.objectives)
            elif k == 'InternalValidator':
                self.internal_validator = self.validator_orchestrator.get_validator(description[k], self.region, self.objectives)

    @Effector.effector("CandidateSelector", identifiers="model_name")
    def _init_candiate_selector(self, description):
        self.candidate_selector = self.candidate_selector_orchestrator.get_candidate_selector(description)

    def _get_descriptions(self, model_description:dict, type_name:str):
        """Return a list with all descriptions of a special type like Optimizer, Surrogate, etc."""
        return [description for key, description in model_description.items() if type_name in key]

    def predict(self, parameters: List[Hyperparameter], configurations: List[Configuration]) -> pd.DataFrame:
        """
        Encapsulates all model related functionality.
        """
        self.created_surrogates_descriptions_and_objectives_and_optimizer_descriptions = []  # clean up descriptions for transfer learning

        # handle multiple objectives
        names_of_parameters = [p.name for p in parameters]

        data = pd.DataFrame(
            [cfg.to_series()[names_of_parameters + list(self.objectives.keys())] for cfg in configurations])

        if data.empty:
            return pd.DataFrame()

        features = pd.DataFrame(data[names_of_parameters])
        labels = pd.DataFrame(data[list(self.objectives.keys())])

        result = []
        # outer split of train and test data
        train_features, train_labels, test_features, test_labels = self.external_validator.train_test_split(features, labels)
        if len(train_features) == 1 and len(train_labels) == 1 and len(test_features) == 1 and len(test_labels) == 1:
            if train_features[0].empty or train_labels[0].empty or test_features[0].empty or test_labels[0].empty:
                return pd.DataFrame(result)

        promising_surrogates: Mapping[Surrogate, Dict] = {}
        for k in range(len(train_features)):
            for s in self.mapping_surrogate_objective.keys():
                considered_objectives = self.mapping_surrogate_objective[s]
                train_labels_filtered = pd.DataFrame(train_labels[k][list(considered_objectives.keys())])

                if self.internal_validator is not None:
                    # inner split
                    inner_train_features, inner_train_labels, inner_test_features, inner_test_labels = (
                        self.internal_validator.train_test_split(train_features[k], train_labels_filtered))

                    if (len(inner_train_features) == 1 and len(inner_train_labels) == 1 and len(
                            inner_test_features) == 1 and len(inner_test_labels) == 1):
                        if (inner_train_features[0].empty or inner_train_labels[0].empty or inner_test_features[0].
                                empty or inner_test_labels[0].empty):
                            continue

                    was_not_built_or_validated = False
                    for k2 in range(len(inner_train_features)):
                        is_built = s.create(inner_train_features[k2], inner_train_labels[k2])
                        if not is_built:
                            was_not_built_or_validated = True
                            continue
                        is_valid, _ = self.internal_validator.validate(s, inner_test_features[k2], inner_test_labels[k2])
                        if not is_valid:
                            was_not_built_or_validated = True
                            continue
                    if was_not_built_or_validated:
                        continue
                    promising_surrogates[s] = considered_objectives
                else:
                    # create surrogate
                    is_built = s.create(train_features[k], train_labels_filtered)
                    if not is_built:
                        return pd.DataFrame()
                    promising_surrogates[s] = considered_objectives

        surrogates_for_outer_validation = []
        if (self.mo_handling_surrogate_type == "Compositional" or self.
                mo_handling_surrogate_type == "DynamicCompositional" or self.mo_handling_surrogate_type == "Portfolio"):
            # extract MO surrogates
            for s, o in promising_surrogates.items():
                if len(o.keys()) > 1:
                    surrogates_for_outer_validation.append(s)
            for s in surrogates_for_outer_validation:
                del promising_surrogates[s]

            # create composite surrogates
            mapping_objective_surrogate: Dict[str, List[Surrogate]] = {}
            for o in self.objectives.keys():
                for s, objective in promising_surrogates.items():
                    if o in objective.keys():
                        if not mapping_objective_surrogate.__contains__(o):
                            mapping_objective_surrogate[o] = [s]
                        else:
                            temp_list = mapping_objective_surrogate[o]
                            temp_list.append(s)
                            mapping_objective_surrogate[o] = temp_list

            comp_surr_input = list(itertools.product(*mapping_objective_surrogate.values()))
            for csi in comp_surr_input:
                if len(csi) != len(self.objectives) or len(csi) == 1:
                    continue
                cs = CompositeSurrogate(csi, self.region)
                surrogates_for_outer_validation.append(cs)
        else:
            for s, o in promising_surrogates.items():
                surrogates_for_outer_validation.append(s)

        # outer validation
        validated_surrogates: Dict[Surrogate, float] = {}
        for s in surrogates_for_outer_validation:
            was_not_built_or_validated = False
            score = 0.0
            for k in range(len(train_features)):
                is_built = s.create(train_features[k], train_labels[k])
                if not is_built:
                    was_not_built_or_validated = True
                    break
                is_valid, score = self.external_validator.validate(s, test_features[k], test_labels[k])
                if not is_valid:
                    was_not_built_or_validated = True
                    break
            if not was_not_built_or_validated:
                validated_surrogates[s] = score

        # sort by validation score
        validated_surrogates = dict(sorted(validated_surrogates.items(), key=lambda item: item[1], reverse=True))

        # create surrogates depending on MO handling type
        created_surrogates = []
        start_time = time.time()

        for s in validated_surrogates:
            b = s.create(features, labels)
            if b:
                created_surrogates.append(s)
            if self.mo_handling_surrogate_type == "DynamicCompositional":
                break

        if len(created_surrogates) == 0:
            return pd.DataFrame()

        self.time_to_build = time.time() - start_time

        # run optimizer, calling the surrogate
        optimized_full = pd.DataFrame()
        if self.mo_handling_surrogate_type != "Compositional":
            for s in created_surrogates:
                for optimizer, objective in self.mapping_optimizer_objective.items():  # always 1 optimizer in 2.6.0
                    self.created_surrogates_descriptions_and_objectives_and_optimizer_descriptions.append(
                        {"Surrogate": s.surrogate_description} | {"Objectives_surrogate": s.objectives} | {
                            "Optimizer": optimizer.optimizer_description} | {"Objectives_optimizer": objective})
                    optimized = optimizer.optimize(s)
                    optimized_full = pd.concat([optimized_full, optimized])
        else:
            composite_surrogate: CompositeSurrogate = created_surrogates[0]
            for s in composite_surrogate.surrogates:
                for optimizer, objective in self.mapping_optimizer_objective.items():
                    if s.objectives == objective:
                        self.created_surrogates_descriptions_and_objectives_and_optimizer_descriptions.append(
                            {"Surrogate": s.surrogate_description} | {"Objectives_surrogate": s.objectives} | {
                                "Optimizer": optimizer.optimizer_description} | {"Objectives_optimizer": objective})
                        optimized = optimizer.optimize(s)
                        optimized_full = pd.concat([optimized_full, optimized])

        # select candidates

        contains_scalarized_surrogate = any([s.scalarized for s in created_surrogates])
        if not contains_scalarized_surrogate:
            names_and_objectives = [r.name for r in self.region] + [o for o in self.objectives.keys()]
        else:
            names_and_objectives = [r.name for r in self.region] + ["Y"]

        selected_candidates = self.candidate_selector.select_candidates(optimized_full[names_and_objectives])

        return pd.DataFrame(selected_candidates)
