from stop_condition.stop_condition_abs import StopCondition
from tools.features_tools import split_features_and_labels
import logging


class StopConditionBO(StopCondition):

    def __init__(self, minimization_task_bool):
        self.logger = logging.getLogger(__name__)
        self.minimization_task_bool = minimization_task_bool

    def validate_solution(self, io, task_config, repeater, default_value, predicted_features):
        self.logger.info("Verifying solution that model gave..")
        if io:
            io.emit('info', {'message': "Verifying solution that model gave.."})

        # "repeater.measure_task" works with list of tasks. "predicted_features" is one task, because of that it is transmitted as list
        solution_candidate = repeater.measure_task([predicted_features], io=io)

        solution_feature, solution_labels = split_features_and_labels(solution_candidate, task_config["FeaturesLabelsStructure"])

        # If our measured energy higher than default best value - add this point to data set and rebuild model.
        #validate false
        if self.minimization_task_bool is True and solution_labels > default_value:
            self.logger.info("Predicted value larger than default: %s > %s" % (solution_labels[0][0], default_value[0][0]))
            prediction_is_final = False
        if self.minimization_task_bool is False and solution_labels < default_value:
            self.logger.info("Predicted value lower than default: %s < %s" % (solution_labels[0][0], default_value[0][0]))
            prediction_is_final = False
        else:
            self.logger.info("Solution validation success!")
            if io:
                io.emit('info', {'message': "Solution validation success!"})
            prediction_is_final = True
        return solution_labels[0], solution_feature[0], prediction_is_final
