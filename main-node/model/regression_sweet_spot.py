import logging

from sklearn import model_selection
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from functools import reduce

from model.model_abs import Model
from core_entities.configuration import Configuration
from tools.front_API import API


class RegressionSweetSpot(Model):

    def __init__(self, log_file_name, experiment):
        """
        Initialization of regression model
        :param log_file_name: - string, location of file, which will store results of model creation
        :param experiment: instance of Experiment class
        """
        self.logger = logging.getLogger(__name__)
        # Send updates to subscribers
        self.sub = API()

        # Model configuration - related fields.
        self.minimal_test_size = experiment.description["ModelConfiguration"]["minimalTestingSize"]
        self.maximal_test_size = experiment.description["ModelConfiguration"]["maximalTestingSize"]
        self.log_file_name = log_file_name

        # Built model - related fields.
        self.model = None
        self.minimum_model_accuracy = experiment.description["ModelConfiguration"]["MinimumAccuracy"]
        self.built_model_accuracy = 0
        self.built_model_test_size = 0.0

        # Data holding fields.
        self.experiment = experiment
        self.all_configurations = []

    def build_model(self, degree=6, tries=20):
        """
        Tries to build the new regression model.

        :param degree: Int. scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PolynomialFeatures.html
        :param tries: Int. Number of tries to build the model in each step of decreasing test size.
        :return: Boolean. True if the model was successfully built, otherwise - False.
        """

        # Building model
        cur_accuracy = 0.99
        best_got = -10e10
        best_model = None
        while cur_accuracy > self.minimum_model_accuracy:
            current_test_size = self.maximal_test_size
            while current_test_size > self.minimal_test_size:
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
                        self.logger.info('GOT NEW ACCURACY: %s with %s test size and %s accuracy threshold ' % (
                            round(score_measured, 3), round(current_test_size, 2), round(cur_accuracy, 2)))

                if best_got > cur_accuracy:
                    self.model = best_model
                    self.built_model_accuracy = best_got
                    self.built_model_test_size = current_test_size
                    self.logger.info("Regression model built with %s test size and %s accuracy." % (
                        current_test_size, best_got))
                    return True
                else:
                    current_test_size -= 0.01
            cur_accuracy -= 0.01
        self.logger.info("Unable to build model, current best accuracy: %s need more data.." % best_got)
        return False

    def validate_model(self, degree=6):
        """
        Return True, if the model have built, and False, if the model can not build or the model already exists
        :param degree:
        :return: True or False
        """
        # Check if model was built.
        if not self.model:
            return False

        self.test_model_all_data(self.experiment.search_space.copy())

        # Check if the model is adequate - write it.
        predicted_configuration = self.predict_next_configurations(1)
        predicted_labels = predicted_configuration[0].predicted_result
        if predicted_labels[0] >= 0:
            f = open(self.log_file_name, "a")
            f.write("Search space::\n")
            f.write(str(self.experiment.search_space) + "\n")
            f.write("Testing size = " + str(self.built_model_test_size) + "\n")
            for i in range(degree + 1):
                if i == 0:
                    f.write("(TR ^ 0) * (FR ^ 0) = " + str(self.model.named_steps['reg'].coef_[i]) + "\n")
                else:
                    for j in range(i + 1):
                        f.write("(TR ^ " + str(i - j) + ") * (FR ^ " + str(j) + ") = " +
                                str(self.model.named_steps['reg'].coef_[0][self.sum_fact(i) + j]) + "\n")
            f.write("R^2 = " + str(self.built_model_accuracy) + "\n")
            f.write("Intercept = " + str(self.model.named_steps['reg'].intercept_) + "\n")
            f.close()
            self.logger.info("Built model is valid.")
            self.sub.send('log', 'info', message="Built model is valid")
            return True
        else:
            self.logger.info("Predicted energy lower than 0: %s. Need more data.." % predicted_labels[0])
            self.sub.send('log', 'info', message="Predicted energy lower than 0: %s. Need more data.." % predicted_labels[0])
            return False

    def predict_next_configurations(self, amount):
        """
        Takes features, using previously created model makes regression to find labels and return label with the lowest value.
        :param amount: int number of Configurations which will be returned
        :return: list of Configurations that are needed to be measured.
        """
        # 1. get model's predictions
        predicted_results = []
        for index, predicted_result in sorted(enumerate(self.model.predict(self.experiment.search_space)), key=lambda c :c[1]):
            conf = self.experiment.search_space[index]
            predicted_results.append((predicted_result, conf))

        # Only for DEMO 
        # self.sub.send('predictions', 'configurations',
        #               configurations=[self.experiment.search_space[index] for (predicted_result, index) in predicted_results],
        #               results=[[round(predicted_result[0], 2)] for (predicted_result, index) in predicted_results])
        
        # 2. Update predicted results for already evaluated Configurations.
        for config in self.all_configurations:
            for pred_tuple in predicted_results:
                if(pred_tuple[1] == config.get_parameters()):
                    config.add_predicted_result(pred_tuple[1], pred_tuple[0])

        # 3. Pick up requared amount of configs
        all_config = [conf.get_parameters() for conf in self.all_configurations]
        result = []
        for best in predicted_results[:amount]:
            if best[1] in all_config:
                select = [conf for conf in self.all_configurations if conf.get_parameters() == best[1]]
                result.append(select[0])
            else:
                new_conf = Configuration(best[1])
                new_conf.add_predicted_result(best[1], best[0])
                result.append(new_conf)

        # 4. return configs
        return result


    def resplit_data(self, test_size):
        """
        Just recreates subsets of features and labels for training and testing from existing features and labels.
        :param test_size: Float. Indicates the amount of data that will be used to test the model.
        :return: None
        """
        all_features = []
        all_labels = []
        for configuration in self.all_configurations:
            all_features.append(configuration.get_parameters())
            all_labels.append(configuration.get_average_result())

        feature_train, feature_test, target_train, target_test = \
            model_selection.train_test_split(all_features, all_labels, test_size=test_size)

        return feature_train, feature_test, target_train, target_test

    @staticmethod
    def sum_fact(num):
        """
        Return the sum of all numbers from 1 till 'num'
        :param num: int
        :return:
        """
        return reduce(lambda x, y: x+y, list(range(1, num + 1)))

    def test_model_all_data(self, search_space):
        """

        :param search_space: list of dimensions for this experiment
                             shape - list of lists, e.g. ``[[1, 2, 4, 8, 16, 32], [1200.0, 1300.0, 2700.0, 2900.0]]``
                                     if there is such search space in "taskData.json" :
                                         {
                                             "threads": [1, 2, 4, 8, 16, 32],
                                             "frequency": [1200.0, 1300.0, 2700.0, 2900.0]
                                         }
        """
        from tools.features_tools import split_features_and_labels
        from tools.splitter import Splitter
        all_data = []

        file_path = "./csv/" + self.experiment.description["TaskConfiguration"]["WorkerConfiguration"]["ws_file"]
        spl = Splitter(file_path)
        for config in self.all_configurations:
            if config.get_parameters() in search_space:
                search_space.remove(config.get_parameters())
        for point in search_space:
            spl.search(str(point[0]), str(point[1]))
            all_data += [[float(x['FR']), int(x['TR']), float(x['EN'])] for x in spl.new_data]
        features, labels = split_features_and_labels(all_data, ['feature', 'feature', 'label'])
        # from sklearn.model_selection import train_test_split
        score = self.model.score(features, labels)

        self.logger.info("FULL MODEL SCORE: %s. Measured with %s points" % (str(score), str(len(features))))

    def update_data(self, configurations):
        """
        Method adds configurations to whole set of configurations.

        :param configurations: List of Configuration's instances
        :return: self
        """
        self.all_configurations = configurations
        return self
