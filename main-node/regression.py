from sklearn import model_selection
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline

from functools import reduce
import sobol_seq
import numpy


class Regression:

    def __init__(self, output_filename, test_size, features, targets):
        """
        Initialization of regression model. It will
        :param output_filename: - reserved :D
        :param test_size: float number, displays size of test data set
        :param features:  features in machine learning meaning selected by Sobol
        :param targets: labels in machine learning meaning selected by Sobol
        """

        self.test_size = test_size
        self.all_features = features
        self.all_targets = targets
        self.filename = output_filename
        self.model = None
        self.accuracy = 0
        self.solution_ready = False
        self.solution_features = None
        self.solution_labels = None
        self.feature_result = None

    def resplitData(self):
        """
        Just recreates subsets of features and labels for training and testing from existing features and labels.
        :return: None
        """

        self.feature_train, self.feature_test, self.target_train, self.target_test = \
            model_selection.train_test_split(self.all_features, self.all_targets, test_size=self.test_size)

    def build_model(self, degree, score_min, tries=10):
        """
        This function will try to build model that will provide needed accuracy. Each time 10 times resplitting the data
        and going from the best accuracy (0.99) to the worst (score_min param).
        :param degree: Int, see http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PolynomialFeatures.html
        :param score_min: Float, 0.5 < r2_min < 1.0 - Accuracy threshold for model estimation.
        :param tries: int, number of times to try to generate model
        :return: Bool True if created model has needed accuracy, False if not.
        """

        best_got = -10e10
        best_model = None
        while self.test_size > 0.3:
            for x in range(tries):
                self.resplitData()
                model = Pipeline([('poly', PolynomialFeatures(degree=degree, interaction_only=False)), ('reg', Ridge())])
                model.fit(self.feature_train, self.target_train)
                score_measured = model.score(self.feature_test, self.target_test)

                if score_measured > best_got:
                    best_got = score_measured
                    best_model = model
                    print('GOT NEW ACCURACY: %s' %score_measured)


            if best_got > score_min:
                self.model = best_model
                self.accuracy = best_got
                print("Regression model built with %s test size and %s accuracy! Verifying.." % (self.test_size, self.accuracy))
                return True
            else:
                self.test_size -= 0.01
        return False

    def build_model_BRISE(self, degree, score_min, tries=20):
        cur_accuracy = 0.99
        best_got = -10e10
        best_model = None
        init_test_size = self.test_size
        while cur_accuracy > score_min:
            self.test_size = init_test_size
            while self.test_size > 0.3:
                for x in range(tries):
                    self.resplitData()
                    model = Pipeline([('poly', PolynomialFeatures(degree=degree, interaction_only=False)), ('reg', Ridge())])
                    model.fit(self.feature_train, self.target_train)
                    score_measured = model.score(self.feature_test, self.target_test)

                    if score_measured > best_got:
                        best_got = score_measured
                        best_model = model
                        print('GOT NEW ACCURACY: %s with %s test size and %s accuracy threshold ' % (score_measured, round(self.test_size,2), round(cur_accuracy,2)))
                    # print("Accuracy: %s, test size: %s, try: %s" % (cur_accuracy, test_size, x))
                if best_got > cur_accuracy:
                    self.model = best_model
                    self.accuracy = best_got
                    print("Regression model built with %s test size and %s accuracy! Verifying.." % (self.test_size, self.accuracy))
                    return True
                else:
                    self.test_size -= 0.01
            cur_accuracy -= 0.01
        print("Unable to build model, current best accuracy: %s need more data.." % best_got)
        return False

    def regression(self, param, score_min, searchspace, degree=6):

        # Build model if was not built.
        if not self.model:
            if not self.build_model_BRISE(degree, score_min=score_min):
                print("Unable to buld regression model, need more data.")
                self.solution_ready = False
                return False

        # Build regression.
        self.target_result, self.feature_result = self.find_optimal(searchspace)
        self.test_model_all_data(searchspace)

        # Check if the model is adequate - write it.
        if self.target_result[0] >= 0:
            f = open(self.filename, "a")
            f.write("Parameters:\n")
            f.write(str(param)+"\n")
            f.write("Testing size = " + str(self.test_size) + "\n")
            # f.write("Degree = " + str(degree)+ "\n")
            for i in range(degree+1):
                if i == 0:
                    f.write("(TR ^ 0) * (FR ^ 0) = " + str(self.model.named_steps['reg'].coef_[i]) + "\n")
                else:
                    for j in range(i+1):
                        f.write("(TR ^ " + str(i - j) + ") * (FR ^ " + str(j) + ") = " + \
                                str(self.model.named_steps['reg'].coef_[0][self.sum_fact(i)+j])+ "\n")
            f.write("R^2 = " + str(self.model.score(self.feature_test, self.target_test))+"\n")
            f.write("Intercept = " + str(self.model.named_steps['reg'].intercept_)+"\n")
            f.close()
            self.solution_ready = True
            self.solution_labels = self.target_result
            self.solution_features = self.feature_result
            return True
        else:
            self.solution_ready = False
            print("Predicted energy lower than 0: %s. Need more data.." % self.target_result[0])
            return False

    def find_optimal(self, features):
            """
            Takes features, using previously created model makes regression to find labels and return label with the lowest value.
            :param features: list of data points (each data point is also a list).
            :return: lowest value, and related features.
            """
            val, idx = min((val,idx) for (idx,val) in enumerate(self.model.predict(features)))
            return val, features[idx]

    def sum_fact(self, num):
            return reduce(lambda x,y: x+y, list(range(1 ,num + 1)))

    def test_model_all_data(self, search_space):
        from tools.features_tools import split_features_and_labels
        from tools.initial_config import load_task
        from tools.splitter import Splitter

        all_data = []
        file_path = "./csv/" + load_task()["params"]["FileToRead"]
        spl = Splitter(file_path)

        for point in self.all_features:
            if point in search_space:
                search_space.remove(point)

        for point in search_space:
            spl.search(str(point[0]), str(point[1]))
            all_data += [[float(x['FR']), int(x['TR']), float(x['EN'])] for x in spl.new_data]

        features, labels = split_features_and_labels(all_data, ['feature','feature','label'])
        # from sklearn.model_selection import train_test_split

        score = self.model.score(features, labels)
        print("FULL MODEL SCORE: %s. Measured with %s points" % (str(score), str(len(features))))
