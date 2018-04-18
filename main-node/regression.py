__author__ = 'dmitrii'

import csv
from sklearn import model_selection
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline

from functools import reduce

#TODO: comparing to a random version need to throw away old indices staff; change random to specific(see paper)

class Regression:
    dict = []
    features_list = ["EN", "TR", "FR"]
    test_color = "r"
    train_color = "b"
    features = []
    indices = []
    r2 = 0
    # feature_train = []
    # target_train = []
    # feature_test = []
    # target_test = []

    def __init__(self, file_name, train_size, feature_subset, target_subset):
        """
        Initialization of regression model. It will
        :param file_name: - reserved :D
        :param train_size: float number, displays size of training data set
        :param feature_subset: ndarray! features in machine learning meaning selected by Sobol
        :param target_subset: ndarray! labels in machine learning meaning selected by Sobol
        """

        self.train_size = train_size

        self.feature_train, self.feature_test, self.target_train, self.target_test = \
            model_selection.train_test_split(feature_subset, target_subset, train_size=train_size)

    def regression(self, filename, param, degree, r2_min):
        """
        1. Creating regression model based on Pipeline algorithm.
        2. Training model using self.features_train and self.target_train
        3. Model estimation using self.feature_test and self.target_test.
        4. If model is good enough (score > than some target threshold (e.g. 80%):
            4.1. Write as output:
                    To the file "output_"+str(degree)+".txt" - size of fraining data, degree, model regression formula, score and etc.
            4.2 Write results -
        :param filename: String, source file where data for ML is located and used to write output
        :param param: String, parameters for task that was performed (like sleep for 5 seconds, where 5 seconds is the parameter).
        :param degree: Int, see http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PolynomialFeatures.html
        :param r2_min: Float, 0.5 < r2_min < 1.0 - Accuracy threshold for model estimation.
        :return:
        """

        model = Pipeline([('poly', PolynomialFeatures(degree=degree, interaction_only=False)), ('reg', Ridge())])
        #
        # print self.feature_train
        # print self.target_train

        print(self.feature_train)
        model.fit(self.feature_train, self.target_train)

        r2 = model.score(self.feature_test, self.target_test)
        self.r2 = r2
        print(filename)
        print(param)
        print(degree)
        print(r2)
        print(r2_min)
        if (r2 > r2_min):
            f = open("output_"+str(degree)+".txt", "a")
            f.write(filename+"\n")
            f.write(param+"\n")
            f.write("Training size = " + str(self.train_size) + "\n")
            f.write("Degree = " + str(degree)+ "\n")
            for i in range(degree+1):
                if i == 0:
                    f.write("(TR ^ 0) * (FR ^ 0) = " + str(model.named_steps['reg'].coef_[i]) + "\n")
                else:
                    for j in range(i+1):
                        f.write("(TR ^ " + str(i - j) + ") * (FR ^ " + str(j) + ") = " + \
                            str(model.named_steps['reg'].coef_[self.sum_fact(i)+j])+ "\n")

            f.write("R^2 = " + str(model.score(self.feature_test, self.target_test))+"\n")
            f.write("Intercept = " + str(model.named_steps['reg'].intercept_)+"\n")


            self.ind_len = len(self.indices)
            f.close()
            self.model = model
            data = []

            with open("tmp"+filename[4:-8]+"_"+param+".csv", 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    data.append(row)
            with open("subsets/"+filename[4:-4]+"_"+param+"_"+str(len(self.indices))+".csv", 'ab') as result:
                fieldnames = list(data[0].keys())
                writer = csv.DictWriter(result, dialect='excel', fieldnames= fieldnames)
                writer.writeheader()
                for i in range(len(data)):
                    if self.indices.__contains__(i):
                        writer.writerow(data[i])

            return True
        return False

    def find_optimal(self, features):
        freqs = [1200., 1300., 1400., 1600., 1700., 1800., 1900., 2000., 2200., 2300., 2400., 2500., 2700., 2800., 2900., 2901.]
        threads = [1., 2., 4., 8., 16., 32.]
        # threads = [1.,2.,3.,4.,5.,6.,7.,8.,9.,10.,11.,12.,13.,14.,15.,16.,17.,18.,19.,20.,21.,22.,23.,24.,25.,26.,27.,28.,29.,30.,31.,32.]
        #print self.model.decision_function(features)
        #print len(features)
        val, idx = min((val,idx) for (idx,val) in enumerate(self.model.decision_function(features)))
        #print val
        #print idx
        #val_act, idx_act = min((val_act,idx_act) for (idx_act,val_act) in enumerate(target))
        #print val_act
        #print idx_act
        #print features[idx_act]
        #print features[idx]
        #print self.model.decision_function(features)[idx_act]
        return val, features[idx]
            #for f in freqs:
            #    for t in threads:
            #        if f == 1200. and t == 1.:
            #            optimal_energy = self.model.predict(np.array([t,f]))[0]
            #            optimal_config = np.array([t,f])
            #            #print optimal_energy
            #            continue
            #        en = self.model.predict(np.array([t,f]))[0]
            #        #print en
            #        if en < optimal_energy:
            #            optimal_energy = en
            #            optimal_config = np.array([t,f])

            #print optimal_config
            #print optimal_energy
            #return optimal_energy, optimal_config



    def sum_fact(self, num):
        return reduce(lambda x,y: x+y, list(range(1 ,num + 1)))
