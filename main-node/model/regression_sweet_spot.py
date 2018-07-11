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

    def resplitData(self):
        """
        Just recreates subsets of features and labels for training and testing from existing features and labels.
        :return: None
        """

        self.feature_train, self.feature_test, self.target_train, self.target_test = \
            model_selection.train_test_split(self.all_features, self.all_targets, test_size=self.test_size)

    def build_model_BRISE(self, socket_client, degree, score_min, tries=20):
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
                        print('GOT NEW ACCURACY: %s with %s test size and %s accuracy threshold ' % (round(score_measured,3), round(self.test_size,2), round(cur_accuracy,2)))
                    # print("Accuracy: %s, test size: %s, try: %s" % (cur_accuracy, test_size, x))
                if best_got > cur_accuracy:
                    self.model = best_model
                    
                    msg = str(best_model).encode()
                    socket_client.sendall(msg)
                    
                    self.accuracy = best_got
                    print("Regression model built with %s test size and %s accuracy! Verifying.." % (self.test_size, self.accuracy))
                    return True
                else:
                    self.test_size -= 0.01
            cur_accuracy -= 0.01
        print("Unable to build model, current best accuracy: %s need more data.." % best_got)
        return False

    def build_model(self, socket_client, param, score_min, searchspace, degree=6):

        # Build model if was not built.
        if not self.model:
            if not self.build_model_BRISE(socket_client, degree, score_min=score_min):
                print("Unable to build regression model, need more data.")
                self.solution_ready = False
                return False

        # Build regression.
        self.solution_labels, self.solution_features = self.find_optimal(searchspace, socket_client)
        self.test_model_all_data(searchspace)

        # Check if the model is adequate - write it.
        if self.solution_labels[0] >= 0:
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
            return True
        else:
            self.solution_ready = False
            print("Predicted energy lower than 0: %s. Need more data.." % self.solution_labels[0])
            return False

    def find_optimal(self, features, socket_client):
            """
            Takes features, using previously created model makes regression to find labels and return label with the lowest value.
            :param features: list of data points (each data point is also a list).
            :return: lowest value, and related features.
            """

            msg = str("** Regression").encode()
            socket_client.sendall(msg)
    
            for (idx,val) in enumerate(self.model.predict(features)):
                msg = str(features[idx]) + str(' = ') + str(val) + "\n"
                print ("---- reg:  " + msg)
                msg = msg.encode()
                socket_client.sendall(msg)
                msg = ""

            msg = str("** Regression end").encode()
            socket_client.sendall(msg)

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

    def validate(self, socket_client, success, task, repeater, selector, default_value, default_result, search_space, features, labels):
        if success:
            # validate() in regression
            print("Model build with accuracy: %s" % self.accuracy)
            print("Verifying solution that model gave..")
            real_result = split_features_and_labels(repeater.measure_task([self.solution_features], socket_client), task["params"]["ResultFeatLabels"])[1][0]

            # If our measured energy higher than default best value - add this point to data set and rebuild model.
            #validate false
            if real_result > default_value[0]:
                features += [self.solution_features]
                labels += [real_result]
                print("Predicted energy larger than default.")
                print("Predicted energy: %s. Measured: %s. Default configuration: %s" %(self.solution_labels[0], real_result[0], default_value[0][0]))
                success = False
            return features, labels, real_result, success

        if not success:
            # get new point from selection alg
            print("New data point needed to continue building regression. Current number of data points: %s" % str(selector.numOfGeneratedPoints))
            print('='*100)
            # cur_task = [sobol.getNextPoint()]
            cur_task = [selector.get_next_point() for x in range(task['params']['step'])]
            if self.solution_features:
                cur_task.append(self.solution_features)
            results = repeater.measure_task(cur_task, socket_client, default_point=default_result[0])
            new_feature, new_label = split_features_and_labels(results, task["params"]["ResultFeatLabels"])
            features += new_feature
            labels += new_label
            # fail rip
            if len(features) > len(search_space):
                print("Unable to finish normally, terminating with best results")
                self.solution_labels = min(labels)
                self.solution_features = features[labels.index(self.solution_labels)]
                print("Measured best config: %s, energy: %s" % (str(self.solution_features), str(self.solution_labels)))
                success = True
            return features, labels, self.solution_labels, success

    def get_new_point(self):
        pass

    def get_result(self, features, repeater, measured_energy):
        print("\n\nPredicted energy: %s, with configuration: %s" % (self.solution_labels[0], self.solution_features))
        print("Number of measured points: %s" % len(features))
        print("Number of performed measurements: %s" % repeater.performed_measurements)
        print("Measured energy is: %s" % str(measured_energy[0]))
        return self.solution_labels, self.solution_features