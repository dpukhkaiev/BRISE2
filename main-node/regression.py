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

    def build_model(self, degree, score_min, tries=20):
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
        self.test_mode_all_data(searchspace)

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

    def test_mode_all_data(self, search_space, data_file = '/media/sem/B54BE5B22C0D3FA8/GoogleDrive/Master thesis/code/worker/csv_data/Radix-1000mio.csv'):
        import sys
        from main import feat_lab_split
        sys.path.insert(0, "../worker/csv_data")
        from splitter import Splitter
        all_data = []
        spl = Splitter(data_file)

        for point in self.all_features:
            if point in search_space:
                search_space.remove(point)

        for point in search_space:
            spl.search(str(point[0]), str(point[1]))
            all_data += [[float(x['FR']),float(x['TR']),float(x['EN'])] for x in spl.new_data]

        features, labels = feat_lab_split(all_data, ['feature','feature','label'])
        # from sklearn.model_selection import train_test_split

        score = self.model.score(features, labels)
        print("FULL MODEL SCORE: %s. Measured with %s points" % (str(score), str(len(features))))

class SobolSequence():

    def __init__(self, dimensionality, data):
        """
        Creates SobolSequence instance that stores information about number of generated poitns
        :param dimensionality: - number of different parameters in greed.

        """
        self.dimensionality = dimensionality
        self.data = data
        self.numOfGeneratedPoints = 0

    def __generate_sobol_seq(self, number_of_data_points=1, skip = 0):
        """
            Generates sobol sequence of uniformly distributed data points in N dimensional space.
            :param number_of_data_points: int - number of points that needed to be generated in this iteration
            :return: sobol sequence as numpy array.
        """

        sequence = sobol_seq.i4_sobol_generate(self.dimensionality, skip + number_of_data_points)[skip:]
        self.numOfGeneratedPoints += number_of_data_points

        return sequence

    def getNextPoint(self):
        """
        Will return next data point from initiated Sobol sequence.
        :return:
        """
        # Cut out previously generated points.
        skip = self.numOfGeneratedPoints

        # Point is a list with floats uniformly distributed between 0 and 1 for all parameters [paramA, paramB..]
        point = self.__generate_sobol_seq(skip=skip)[0]

        result = []
        # In loop below this distribution imposed to real parameter values list.
        for parameter_index, parameterValue in enumerate(point):
            result.append(self.data[parameter_index][round(len(self.data[parameter_index]) * float(parameterValue) - 1 )])

        return result

    def mergeDataWithSobolSeq(self, sobol_seq=None, numOfPoints = 'all'):
        """
        Method maps input parameter points to uniformly generated sobol sequence and returns data points.
        Number of parameters should be the same as depth of each point in Sobol sequence.
        It is possible to call method without providing Sobol sequence - it will be generated in runtime.
        :param sobol_seq: data points
        :param numOfPoints: 'all' - all parameters will be mapped to sobol distribution function, or int
        :return: List with uniformly distributed parameters across parameter space.
        """

        if type(sobol_seq) is numpy.ndarray:
            if len(self.data) != len(sobol_seq[0]):
                print("Warning! Number of provided parameters does not match with size of Sobol sequence. Generating own Sobol sequence based on provided parameters.")
                sobol_seq = None

        # The below 'if' case generates sobol sequence
        if not sobol_seq or type(sobol_seq) is not numpy.ndarray:

            if numOfPoints == 'all':
                numOfPoints = 1
                for parameter in self.data:
                    numOfPoints *= len(parameter)

            sobol_seq = self.__generate_sobol_seq(numOfPoints)

        # Following loop apply Sobol grid to given parameter grid, e.g.:
        # for Sobol array(
        #  [[ 0.5  ,  0.5  ],
        #   [ 0.75 ,  0.25 ],
        #   [ 0.25 ,  0.75 ],
        #   [ 0.375,  0.375],
        #   [ 0.875,  0.875]])
        #
        # And params = [
        # [1, 2, 4, 8, 16, 32],
        # [1200.0, 1300.0, 1400.0, 1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2200.0, 2300.0, 2400.0, 2500.0, 2700.0, 2800.0,
        #   2900.0, 2901.0]
        #               ]
        # We will have output like:
        # [[3.0, 8.0],
        #  [4.5, 4.0],
        #  [1.5, 12.0],
        #  [2.25, 6.0],
        #  [5.25, 14.0]]
        result = []
        for point in sobol_seq:
            tmp_res = []
            for parameter_index, parameterValue in enumerate(point):
                tmp_res.append(self.data[parameter_index][round(len(self.data[parameter_index]) * float(parameterValue) - 1 )])
            result.append(tmp_res)
        return result

