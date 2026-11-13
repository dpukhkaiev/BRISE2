"""
The transformation of configurations for the surrogates and the optimizers of a region.

A surrogate or an optimizer holds a mapping from its configuration transformers to the parameters of the region each
one serves. The functions here build that mapping, transform configurations with it and transform an optimizer's
proposals back into configurations. The surrogate's transformers also know the inactive value of the parameters
that are activated within the region (a flat region), the optimizer's don't.
"""
from typing import Dict, Iterable, Mapping, Tuple

import pandas as pd

from configuration_selection.model.configuration_transformer.configuration_transformer_abs import ConfigurationTransformer
from configuration_selection.model.configuration_transformer.configuration_transformer_orchestrator import ConfigurationTransformerOrchestrator
from core_entities.search_space import Hyperparameter, active_mask


def build_transformers(description: Dict, region: Tuple[Hyperparameter],
                       parameters_with_inactive_value: frozenset = frozenset()
                       ) -> Dict[ConfigurationTransformer, Tuple[Hyperparameter]]:
    """
    :param description: description of a surrogate or an optimizer, with its 'ConfigurationTransformers' if it has any.
    :param region: the parameters of the region.
    :param parameters_with_inactive_value: names of the parameters whose transformers also transform the inactive value.
    :return: every configuration transformer of the description with the parameters of the region it serves, the ones
    of its type.
    """
    orchestrator = ConfigurationTransformerOrchestrator()
    transformers = {}
    for i in description.items():
        if "ConfigurationTransformer" in i[0]:
            for ct in i[1].items():
                relevant_parameters = tuple(filter(lambda r: r.type in ct[0], region))
                configuration_transformer = orchestrator.get_configuration_transformer(
                    ct, relevant_parameters, parameters_with_inactive_value)
                transformers[configuration_transformer] = relevant_parameters
    return transformers


def write_inactive_values(features: pd.DataFrame, conditional_parameters: Iterable[Hyperparameter]) -> pd.DataFrame:
    """
    Write the inactive value into the cells of inactive parameters.
    :param features: configurations, one per row, with a column per parameter; a missing parameter holds NaN.
    :param conditional_parameters: the parameters that are activated within the region, none in a hierarchical one.
    :return: features with the inactive value in the cells of inactive parameters.
    """
    conditional_parameters = list(conditional_parameters)
    if not conditional_parameters:
        return features
    mask = active_mask(features, [hp.activation_condition for hp in conditional_parameters])
    features = features.copy()
    for hp in conditional_parameters:
        if hp.name in features.columns:
            inactive = ~mask[hp.name]
            if inactive.any():
                features[hp.name] = features[hp.name].astype(object)
                features.loc[inactive, hp.name] = hp.inactive_value()
    return features


def transform(features: pd.DataFrame, transformers: Mapping[ConfigurationTransformer, Tuple[Hyperparameter]],
           conditional_parameters: Iterable[Hyperparameter] = ()) -> pd.DataFrame:
    """
    :param features: configurations, one per row, with a column per parameter.
    :param transformers: the configuration transformers with the parameters each serves.
    :param conditional_parameters: the parameters whose cells hold the inactive value where they are inactive, none for
    an optimizer.
    :return: the transformed features, by position of the rows.
    """
    features = write_inactive_values(features.reset_index(drop=True), conditional_parameters)
    if len(transformers) > 0:
        transformed_names = sum([[hp.name for hp in p] for p in transformers.values()], [])
        transformed_features = pd.DataFrame()
        for f_name in features.columns:
            if f_name in transformed_names:
                for ct, p in transformers.items():
                    for hp in p:
                        if hp.name == f_name:
                            transformed_relevant_features = ct.transform(pd.DataFrame(features.loc[:, hp.name]))
                            if transformed_features.empty:
                                transformed_features = transformed_relevant_features
                            else:
                                transformed_features = transformed_features.join(transformed_relevant_features)
            else:
                if transformed_features.empty:
                    transformed_features = pd.DataFrame(features.loc[:, f_name])
                else:
                    transformed_features = transformed_features.join(pd.DataFrame(features.loc[:, f_name]))
    else:
        transformed_features = features
    return transformed_features


def inverse_transform(optimized_features: pd.DataFrame,
           transformers: Mapping[ConfigurationTransformer, Tuple[Hyperparameter]]) -> pd.DataFrame:
    """
    :param optimized_features: an optimizer's proposals, one per row, in the representation of its transformers.
    :param transformers: the optimizer's configuration transformers; they learn the columns they produce when they
    transform, so a configuration must have been transformed with them before.
    :return: the proposals as configurations, with the original parameters.
    """
    result = pd.DataFrame()
    involved_features = set()  # features involved in configuration transformers
    for new_hp_name in optimized_features.columns:
        for ct, params in transformers.items():
            for old_f, new_f in ct.mapping_old_new_features.items():
                if new_hp_name not in new_f:
                    continue
                else:
                    inverse_transformed = ct.inverse_transform(
                        optimized_features[ct.mapping_old_new_features[old_f]])
                    if result.empty:
                        result = inverse_transformed
                    elif inverse_transformed.columns[0] not in result.columns:
                        result = result.join(inverse_transformed)
                    involved_features.add(new_hp_name)
        if new_hp_name not in involved_features:  # parameter not in configuration transformers
            if result.empty:
                temp_df = optimized_features.copy()
                temp_df = temp_df[[new_hp_name]]
                result = temp_df
            elif new_hp_name not in result.columns:
                result = result.join(optimized_features[new_hp_name])

    return result
