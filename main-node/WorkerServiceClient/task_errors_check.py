import builtins
import logging

def error_check(tasks, parameter, expected_values_range, expected_data_type):
    """
    Finds and marks values, that could not be used in evaluation
    :param tasks: results value for 1 configuration that should be checked
    :param parameter: results parameter name that should be checked
    :param expected_values_range: specify user-defined limit of correct values. Values that goes beyond are discarded
    :param expected_data_type: specify user-defined type of correct values.
    :return: list of results with marked bad values
    """
    # In this implementation we assume, that values should be numerical (int, float etc)
    # with pattern, described in json experiment file
    if tasks['ResultValidityCheckMark'] == 'OK':
        # this part finds and deletes values with an inappropriate data type
        try:
            # All numerical types could be converted to float
            # Also string with a corresponding pattern (numerical) can be converted
            result_entity_class = getattr(builtins, expected_data_type)
            tasks['result'][parameter] = result_entity_class(tasks['result'][parameter])
        except Exception as e:
            # indexes of other values are fixed in delete array
            tasks['ResultValidityCheckMark'] = "Bad value"
            return tasks
        # this part finds indexes of values ​​that do not match the user-defined pattern
        # define lower and upper limits of expected results (described in json)
        # if limit is not defined, it is automatically sets as infinity
        task_result_value = tasks['result'][parameter]
        try:
            lower_limit = float(expected_values_range[0])
        except Exception as e:
            lower_limit = float("-inf")
        try:
            upper_limit = float(expected_values_range[1])
        except Exception as e:
            upper_limit = float("inf")
        if "nil" in str(task_result_value) or\
        "null" in str(task_result_value) or\
        "nan" in str(task_result_value) or\
        task_result_value < lower_limit or\
        task_result_value > upper_limit:
            tasks['ResultValidityCheckMark'] = "Out of bounds"

    return tasks
