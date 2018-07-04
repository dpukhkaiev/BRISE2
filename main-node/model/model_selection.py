from model.regression_sweet_spot import RegressionSweetSpot
def get_model(model_type, res_storage, file_to_read, model_test_size, features, labels):
    if model_type == "regression":
        return  RegressionSweetSpot(output_filename = "%s%s_regression.txt" % (res_storage, file_to_read),
                         test_size = model_test_size,
                         features = features,
                         targets = labels)
    else:
        raise KeyError