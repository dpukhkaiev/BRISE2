import numpy as np

from outliers.outliers_detector_decorator import OutliersDetectionDecorator


class Quartiles(OutliersDetectionDecorator):

	def __init__(self, outlier_detector, parameters):
		super().__init__(outlier_detector, __name__, parameters)

	def _find_outliers(self, inputs):
		criterion_used_flag = False
		if self.lower_threshold <= len(inputs) <= self.upper_threshold:
			"""
			Sources:
			1. Tukey, John W (1977). Exploratory Data Analysis. Addison-Wesley. ISBN 978-0-201-07616-5.
			2. A Review and Comparison of Methods for Detecting Outliers in Univariate Data Sets
			Songwon Seo BS, Kyunghee University, 2002 


			The rules of the method are as follows:
			1. The IQR (Inter Quartile Range) is the distance between the lower (Q1) and upper (Q3)
			quartiles.
			2. Inner fences are located at a distance 1.5 IQR below Q1 and above Q3 [Q1-1.5 IQR,
			Q3+1.5 IQR].
			3. Outer fences are located at a distance 3 IQR below Q1 and above Q3 [Q1-3 IQR, Q3+3 IQR].
			4. A value between the inner and outer fences is a possible (minor) outlier. 
			An extreme value beyond the outer fences is a probable (major) outlier. 

			There is no statistical basis for the reason that Tukey uses 1.5
			and 3 regarding the IQR to make inner and outer fences. 

			In this realization only outer fences are used, because they are probable outlier (step 2 is skipped)
			"""
			# find limits of quartiles (step 1)
			first_Q = np.percentile(inputs, 25)
			third_Q = np.percentile(inputs, 75)
			Inter_QD = third_Q-first_Q

			# In this realization only outer fences are used, because they are probable outlier (step 2 is skipped)

			# find outer limits (step 3)
			Outer_LB = first_Q - Inter_QD * 3
			Outer_HB = third_Q + Inter_QD * 3

			major_outliers = []

			# step 4
			for i in range(0, len(inputs)):
				if inputs[i] < Outer_LB or inputs[i] > Outer_HB:
					major_outliers.append(inputs[i])

			unique = np.unique(major_outliers)
			criterion_used_flag = True
			return unique, criterion_used_flag
		else:
			return [], criterion_used_flag

