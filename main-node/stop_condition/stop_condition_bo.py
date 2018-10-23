from stop_condition.stop_condition_abs import StopCondition
from tools.features_tools import split_features_and_labels

#передать сюда переменую из класса BayesianOptimization селф.солюшин_лейблз для того,
#  что бы ее продолжать использовать в этом классе
# передать в мейне, получить класс через метод гет_модел

class StopConditionBO(StopCondition):

    def validate_solution(self, io, task_config, repeater, default_value, predicted_features):
        # validate() in regression
        print("Verifying solution that model gave..")
        if io:
            io.emit('info', {'message': "Verifying solution that model gave.."})

        # "repeater.measure_task" works with list of tasks. "predicted_features" is one task, because of that it is transmitted as list
        solution_candidate = repeater.measure_task([predicted_features], io=io)

        solution_feature, solution_labels = split_features_and_labels(solution_candidate, task_config["FeaturesLabelsStructure"])

        # If our measured energy higher than default best value - add this point to data set and rebuild model.
        #validate false
        if solution_labels > default_value:
            print("Predicted energy larger than default: %s > %s" % (solution_labels[0][0], default_value[0][0]))
            prediction_is_final = False
        else:
            print("Solution validation success!")
            if io:
                io.emit('info', {'message': "Solution validation success!"})
            prediction_is_final = True
        return solution_labels[0], solution_feature[0], prediction_is_final

        # model.solution_labels = solution_labels[0]
        # model.solution_features = solution_feature[0]
        # return model.solution_labels, prediction_is_final