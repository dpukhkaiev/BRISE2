from sklearn import model_selection
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline

from functools import reduce
import sobol_seq
import numpy

from model.model_abs import Model
from tools.features_tools import split_features_and_labels


class RegressionSweetSpot(Model):

    def __init__(self, log_file_name, model_config):
        """
        Initialization of regression model
        :param log_file_name: - string, location of file, which will store results of model creation
        :param model_config: float number, displays size of test data set
        """

        # Model configuration - related fields.
        self.model_config = model_config
        self.initial_test_size = model_config["ModelTestSize"]
        self.log_file_name = log_file_name

        # Built model - related fields.
        self.model = None
        self.minimum_model_accuracy = model_config["MinimumAccuracy"]
        self.built_model_accuracy = 0
        self.built_model_test_size = 0.0

        # Data holding fields.
        self.all_features = []
        self.all_labels = []
        self.solution_features = []
        self.solution_labels = []

    def build_model(self, features, labels, degree=6, tries=20):
        """

        Method adds new features and labels to whole set of features and labels.
        Afterwards - tries to build the new regression model.

        :param features: List. features in machine learning meaning selected by Sobol
        :param labels: List. labels in machine learning meaning selected by Sobol
        :param degree: Int. scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PolynomialFeatures.html
        :param tries: Int. Number of tries to build the model in each step of decreasing test size.
        :return: Boolean. True if the model was successfully built.
                          False if the input data didn`t pass the validation OR the model was not built successfully.
        """

        # An input validation and updating of the features and labels set.
        # 1. Tests if lists of features and labels are same length.
        # 2. Tests if all lists are nested.
        # 3. Tests if all values of nested fields are ints or floats. (Because regression works only with those data).
        # These all(all(...)..) returns true if all data
        try:

            assert len(features) == len(labels) > 0, \
                "Incorrect length!\nFeatures:%s\nLabels:%s" % (str(features), str(labels))

            assert all(all(isinstance(value, (int, float)) for value in feature) for feature in features), \
                "Incorrect data types in features: %s" % str(features)

            assert all(all(isinstance(value, (int, float)) for value in label) for label in labels), \
                "Incorrect data types in features: %s" % str(labels)

            self.all_features += features
            self.all_labels += labels

        except AssertionError as err:
            # TODO: replace with logger.
            print("ERROR! Regression input validation error:\n%s" % err)
            return False

        # Building model
        cur_accuracy = 0.99
        best_got = -10e10
        best_model = None
        while cur_accuracy > self.minimum_model_accuracy:
            current_test_size = self.initial_test_size
            while current_test_size > 0.3:
                for x in range(tries):
                    feature_train, feature_test, target_train, target_test = self.resplit_data(current_test_size)
                    model = Pipeline(
                        [('poly', PolynomialFeatures(degree=degree, interaction_only=False)), ('reg', Ridge())]
                    )
                    model.fit(feature_train, target_train)
                    score_measured = model.score(feature_test, target_test)

                    if score_measured > best_got:
                        best_got = score_measured
                        best_model = model
                        temp_message = ('GOT NEW ACCURACY: %s with %s test size and %s accuracy threshold ' % (
                            round(score_measured, 3), round(current_test_size, 2), round(cur_accuracy, 2)))
                        print(temp_message)

                    # print("Accuracy: %s, test size: %s, try: %s" % (cur_accuracy, test_size, x))
                if best_got > cur_accuracy:
                    self.model = best_model
                    self.built_model_accuracy = best_got
                    self.built_model_test_size = current_test_size
                    print("Regression model built with %s test size and %s accuracy." % (
                        current_test_size, best_got))
                    return True
                else:
                    current_test_size -= 0.01
            cur_accuracy -= 0.01
        print("Unable to build model, current best accuracy: %s need more data.." % best_got)
        return False

    def validate_model(self, io, search_space, degree=6):

        # Check if model was built.
        if not self.model:
            return False

        self.test_model_all_data(search_space)

        # Check if the model is adequate - write it.
        predicted_labels, predicted_features = self.predict_solution(io, search_space)
        if predicted_labels[0] >= 0:
            f = open(self.log_file_name, "a")
            f.write("Search space::\n")
            f.write(str(search_space) + "\n")
            f.write("Testing size = " + str(self.built_model_test_size) + "\n")
            # f.write("Degree = " + str(degree)+ "\n")
            for i in range(degree+1):
                if i == 0:
                    f.write("(TR ^ 0) * (FR ^ 0) = " + str(self.model.named_steps['reg'].coef_[i]) + "\n")
                else:
                    for j in range(i+1):
                        f.write("(TR ^ " + str(i - j) + ") * (FR ^ " + str(j) + ") = " + \
                                str(self.model.named_steps['reg'].coef_[0][self.sum_fact(i)+j])+ "\n")
            f.write("R^2 = " + str(self.built_model_accuracy)+"\n")
            f.write("Intercept = " + str(self.model.named_steps['reg'].intercept_)+"\n")
            f.close()
            print("Built model is valid.")
            if io:
                io.emit('info', {'message': "Built model is valid"})
            return True
        else:
            print("Predicted energy lower than 0: %s. Need more data.." % predicted_labels[0])
            return False

    def predict_solution(self, io, search_space):
            """
            Takes features, using previously created model makes regression to find labels and return label with the lowest value.
            :param search_space: list of data points (each data point is also a list).
            :return: lowest value, and related features.
            """

            predictions = [[label, index] for (index, label) in enumerate(self.model.predict(search_space))]
            if io:
                all_predictions = [{'configuration': search_space[index], "prediction": round(prediction[0], 2)}
                                   for (prediction, index) in predictions]
                io.emit('regression', {"regression": all_predictions})
            label, index = min(predictions)
            return label, search_space[index]

    def validate_solution(self, io, task_config, repeater, default_value, predicted_features):
        # validate() in regression
        print("Verifying solution that model gave..")
        if io:
            io.emit('info', {'message': "Verifying solution that model gave.."})
        solution_candidate = repeater.measure_task([predicted_features], io=io)
        solution_feature, solution_labels = split_features_and_labels(solution_candidate, task_config["FeaturesLabelsStructure"])
        # If our measured energy higher than default best value - add this point to data set and rebuild model.
        #validate false
        if solution_labels > default_value:
            print("Predicted energy larger than default.")
            print("Predicted energy: %s. Measured: %s. Default configuration: %s" %(
                predicted_features[0], solution_labels[0][0], default_value[0][0]))
            prediction_is_final = False
        else:
            print("Solution validation success!")
            if io:
                io.emit('info', {'message': "Solution validation success!"})
            prediction_is_final = True
        self.solution_labels = solution_labels[0]
        self.solution_features = solution_feature[0]
        return self.solution_labels, prediction_is_final

    def resplit_data(self, test_size):
        """
        Just recreates subsets of features and labels for training and testing from existing features and labels.
        :param test_size: Float. Indicates the amount of data that will be used to test the model.
        :return: None
        """

        feature_train, feature_test, target_train, target_test = \
            model_selection.train_test_split(self.all_features, self.all_labels, test_size=test_size)

        return feature_train, feature_test, target_train, target_test

    @staticmethod
    def sum_fact(num):
        return reduce(lambda x, y: x+y, list(range(1, num + 1)))

    def test_model_all_data(self, search_space):
        from tools.features_tools import split_features_and_labels
        from tools.initial_config import load_task
        from tools.splitter import Splitter
        all_data = []

        file_path = "./csv/" + load_task()["ExperimentsConfiguration"]["WorkerConfiguration"]["ws_file"]
        spl = Splitter(file_path)
        for point in self.all_features:
            if point in search_space:
                search_space.remove(point)
        for point in search_space:
            spl.search(str(point[0]), str(point[1]))
            all_data += [[float(x['FR']), int(x['TR']), float(x['EN'])] for x in spl.new_data]
        features, labels = split_features_and_labels(all_data, ['feature', 'feature', 'label'])
        # from sklearn.model_selection import train_test_split
        score = self.model.score(features, labels)


        temp_message = ("FULL MODEL SCORE: %s. Measured with %s points" % (str(score), str(len(features))))
        print(temp_message)

    def get_result(self, repeater, features, labels, io):

        #   In case, if regression predicted final point, that have less energy consumption, that default, but there is
        # point, that have less energy consumption, that predicted - report this point instead predicted.

        print("\n\nFinal report:")

        if not self.solution_labels:
            temp_message = "Optimal configuration was not found. Reporting best of the measured."
            print(temp_message)
            self.solution_labels = min(labels)
            index_of_the_best_labels = self.all_labels.index(self.solution_labels)
            self.solution_features = self.all_features[index_of_the_best_labels]
            if io:
                io.emit('info', {'message': temp_message, "quality": self.solution_labels, "conf": self.solution_features})

        elif min(labels) < self.solution_labels:
            temp_message = ("Configuration(%s) quality(%s), "
                  "\nthat model gave worse that one of measured previously, but better than default."
                  "\nReporting best of measured." %
                  (self.solution_features, self.solution_labels))
            print(temp_message)
            if io:
                io.emit('info', {'message': temp_message, "quality": self.solution_labels, "conf": self.solution_features})

            self.solution_labels = min(labels)
            index_of_the_best_labels = self.all_labels.index(self.solution_labels)
            self.solution_features = self.all_features[index_of_the_best_labels]

        print("ALL MEASURED FEATURES:\n%s" % str(features))
        print("ALL MEASURED LABELS:\n%s" % str(labels))
        print("Number of measured points: %s" % len(self.all_features))
        print("Number of performed measurements: %s" % repeater.performed_measurements)
        print("Best found energy: %s, with configuration: %s" % (self.solution_labels, self.solution_features))

        configuration = [float(self.solution_features[0]), int(self.solution_features[1])]
        value = round(self.solution_labels[0], 2)

        if io:
            temp = {"best point": {'configuration': configuration, 
                    "result": value, 
                    "measured points": self.all_features}
                }
            io.emit('best point', temp)

        return self.solution_labels, self.solution_features