import inspect
from typing import Mapping

from core_entities.search_space import (
    FloatHyperparameter,
    IntegerHyperparameter,
    NominalHyperparameter,
    OrdinalHyperparameter
)
from preprocessing.transformers import SklearnColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler


def build_preprocessing_pipelines(parameters: Mapping, data_description: Mapping) -> [Pipeline, Pipeline]:

    # Add separate steps for different data types:
    # 1. Group all types of hyperparameters
    hyperparameters = {
        "OrdinalHyperparameter": [],
        "NominalHyperparameter": [],
        "IntegerHyperparameter": [],
        "FloatHyperparameter": [],
    }
    for column_name in data_description:
        h = data_description[column_name]['hyperparameter']

        if isinstance(h, OrdinalHyperparameter):
            hyperparameters["OrdinalHyperparameter"].append(column_name)

        elif isinstance(h, NominalHyperparameter):
            hyperparameters["NominalHyperparameter"].append(column_name)

        elif isinstance(h, IntegerHyperparameter):
            hyperparameters["IntegerHyperparameter"].append(column_name)

        elif isinstance(h, FloatHyperparameter):
            hyperparameters["FloatHyperparameter"].append(column_name)

        else:
            raise TypeError(f"Unsupported type of hyperparameter {column_name}: {type(h)}.")

    steps = []
    # 2. define preprocessing for each group
    for h_type_name in hyperparameters:
        if len(hyperparameters[h_type_name]) > 0:
            # if we have a columns with data of this type, need to define a preprocessing

            # 1. fetch requested preprocessing class
            prp_spec: str = parameters[h_type_name]
            prp_class_project = prp_spec.split(".")[0].lower()
            prp_class_name = prp_spec.split(".")[1]
            if prp_class_project == "brise":
                import preprocessing as source_project
            elif prp_class_project == "sklearn":
                import sklearn.preprocessing as source_project
            else:
                raise ValueError(f"{prp_class_project} is an unknown source for preprocessing {prp_spec}.")

            preprocessors = inspect.getmembers(source_project, lambda member: inspect.isclass(member))
            preprocessors = list(filter(lambda x: x[0] == prp_class_name, preprocessors))
            if len(preprocessors) < 1:
                raise ValueError(f"Class {prp_class_name} was not found in {source_project}.")
            else:
                prp_class = preprocessors[0][1]

                # 2. Instantiate preprocessor
                if "Ordinal" in h_type_name or "Nominal" in h_type_name:
                    all_categories = []
                    for h_name in hyperparameters[h_type_name]:
                        all_categories.append(data_description[h_name]["categories"])
                    prp = prp_class(categories=all_categories)
                else:
                    # "Integer" in h_type_name or "Float" in h_type_name:
                    prp = prp_class()
                prp = SklearnColumnTransformer(prp, input_column_names=hyperparameters[h_type_name])
                encoder_name = f"{prp} for {hyperparameters[h_type_name]}"

                # 3. Add it to pipeline
                steps.append((encoder_name, prp))

    features_pipeline = Pipeline(steps=steps)
    labels_pipeline = Pipeline(steps=[("labels_min_max_scaler", SklearnColumnTransformer(MinMaxScaler()))])
    return features_pipeline, labels_pipeline
