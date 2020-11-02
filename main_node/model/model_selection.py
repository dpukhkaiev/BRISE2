from typing import Mapping, Union

from model.model_abs import Model


def get_model(model_description: Mapping[str, Union[str, Mapping]]) -> Model:

    # Getting the Class object
    model_type = model_description["Type"]
    if "sklearn" in model_type:
        import inspect

        from model.sklearn_model_wrapper import SklearnModelWrapper
        from sklearn import linear_model

        models = inspect.getmembers(linear_model, lambda member: inspect.isclass(member))
        model_name = model_type.split(".")[1]
        model_class = models[[name_and_class[0] for name_and_class in models].index(model_name)][1]
        sklearn_model = model_class(**model_description["Parameters"]["UnderlyingModelParameters"])
        model = SklearnModelWrapper(sklearn_model, model_description["Parameters"])

    else:
        # trying to find the model class in "model" folder
        from tools.reflective_class_import import reflective_class_import

        model_name = model_type.split(".")[1]
        model_class = reflective_class_import(model_name, "model")
        model = model_class(model_description["Parameters"])

    # Instantiating the Class
    return model
