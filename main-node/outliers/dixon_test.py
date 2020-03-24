import numpy as np

from outliers.outliers_detector_decorator import OutliersDetectionDecorator

class Dixon(OutliersDetectionDecorator):
    def __init__(self, outlier_detector, parameters):
        super().__init__(outlier_detector, __name__, parameters)

    def _find_outliers(self, inputs):
        criterion_used_flag = False
        if self.lower_threshold <= len(inputs) <= self.upper_threshold:
            if len(inputs) <= 30:
                # Dixon table values for 3 different confidence intervals
                q90 = [0.941, 0.765, 0.642, 0.56, 0.507, 0.468, 0.437, 
                    0.412, 0.392, 0.376, 0.361, 0.349, 0.338, 0.329, 
                    0.32, 0.313, 0.306, 0.3, 0.295, 0.29, 0.285, 0.281, 
                    0.277, 0.273, 0.269, 0.266, 0.263, 0.26
                    ]

                q95 = [0.97, 0.829, 0.71, 0.625, 0.568, 0.526, 0.493, 0.466, 
                    0.444, 0.426, 0.41, 0.396, 0.384, 0.374, 0.365, 0.356, 
                    0.349, 0.342, 0.337, 0.331, 0.326, 0.321, 0.317, 0.312, 
                    0.308, 0.305, 0.301, 0.29
                    ]

                q99 = [0.994, 0.926, 0.821, 0.74, 0.68, 0.634, 0.598, 0.568, 
                    0.542, 0.522, 0.503, 0.488, 0.475, 0.463, 0.452, 0.442, 
                    0.433, 0.425, 0.418, 0.411, 0.404, 0.399, 0.393, 0.388, 
                    0.384, 0.38, 0.376, 0.372
                    ]
                # Put coefficients into dictionary for easy search in format key-value 
                # for example (3:0.994)
                # because Dixon test could be applied if at least 3 values exists in dataset
                # and this approach helps to avoid unlogical list indexes usage
                # for example, we need to find Q90 value for 5 points in dataset
                # in case of list we should turn to Q90[2] value
                # in case of dict we turn to value of key "5"
                Q90 = {n:q for n,q in zip(range(3,len(q90)+3), q90)}
                Q95 = {n:q for n,q in zip(range(3,len(q95)+3), q95)}
                Q99 = {n:q for n,q in zip(range(3,len(q99)+3), q99)}
                # Call Dixon outlier function with some confidential interval as input
                outliers = self.dixon_test(inputs, Q95)
                unique = np.unique(outliers)
                criterion_used_flag = True
                return unique, criterion_used_flag
        return [], criterion_used_flag
        
    def dixon_test(self, data, q_dict, left=True, right=True):
        # Dixon test calculates distance between suspicious value and closest one to it
        # Then received value is divided on distance between min and max value in sample
        # and checks this value in coefficient table
        outlierslist = []
        for i in range(0, len(data)):
            # Dixon test could detect only 1 outlier per iteration
            # It could be left-side (lowest values) or right-side (highest values)
            assert(left or right), 'At least one of the variables, `left` or `right`, must be True.'
            if len(data) >= 3:    
                sdata = sorted(data)
                Q_mindiff, Q_maxdiff = (0,0), (0,0)
                # Check left side for outliers    
                if left:
                    Q_min = (sdata[1] - sdata[0]) 
                    try:
                        Q_min /= (sdata[-1] - sdata[0])
                    except ZeroDivisionError:
                        pass
                    Q_mindiff = (Q_min - q_dict[len(data)], sdata[0])
                # check right side for outliers        
                if right:
                    Q_max = abs((sdata[-2] - sdata[-1]))
                    try:
                        Q_max /= abs((sdata[0] - sdata[-1]))
                    except ZeroDivisionError:
                        pass
                    Q_maxdiff = (Q_max - q_dict[len(data)], sdata[-1])
                # if no outlier relation more than table values, stop algorithm
                # there is no outliers
                if not Q_mindiff[0] > 0 and not Q_maxdiff[0] > 0:
                    break
                # if left outlier relation equals right one, 
                # put both points to outlier list    
                elif Q_mindiff[0] == Q_maxdiff[0]:
                    outliers = np.array([Q_mindiff[1], Q_maxdiff[1]])
                    outlierslist.append(outliers)
                # if left outlier relation is more than right one, 
                # put left point to outlier list         
                elif Q_mindiff[0] > Q_maxdiff[0]:
                    outliers = np.array([Q_mindiff[1]])
                    outlierslist.append(outliers)
                # if left outlier relation is less than right one, 
                # put right point to outlier list 
                else:
                    outliers = np.array([Q_maxdiff[1]])
                    outlierslist.append(outliers)
                # remove detected outliers from dataset
                data = np.setdiff1d(data, outliers)

        return outlierslist
