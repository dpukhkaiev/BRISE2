# Outlier Detection.
*This folder contains Basic Outlier Detection class and different outlier detection criteria, 
which are implemented as wrappers around the Basic Outlier Detection class. When you specify an Outlier Detector in 
the Experiment description file, `outliers_detector_selector.py` reads a description and builds an Outlier Detection object.*

In the current implementation, one or more Tasks within related Configuration could be marked as outliers **iff** 
a majority (50% or more) of outlier detectors will mark these values as outliers.

## Variants of Outlier Detectors

All of the outlier detectors should be configured with `OutliersDetection["MinActiveNumberOfTasks"]` 
and `OutliersDetection["MinActiveNumberOfTasks"]` parameters. 
The Dixon outlier Test is used as an example below, but the same structure should be used for all other outlier detectors.

```json
"OutliersDetection":[
    {
      "Type": "Dixon",
      "Parameters": {
        "MinActiveNumberOfTasks": 3,
        "MaxActiveNumberOfTasks": 30
      }
    }
  ]
```

#### Quartiles Based Outlier Detector

Detailed information about this outlier detection criteria could be found at:
  1. Tukey, John W (1977). Exploratory Data Analysis. Addison-Wesley. ISBN 978-0-201-07616-5.
  2. A Review and Comparison of Methods for Detecting Outliers in Univariate Data Sets
  Songwon Seo BS, Kyunghee University, 2002 

#### Mediane Absolute Deviation Based Outlier Detector

Detailed information about this outlier detection criteria could be found at:
  Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and Handle Outliers", 
  The ASQC Basic References in Quality Control: Statistical Techniques, Edward F. Mykytka, Ph.D., Editor. 

#### Chauvenet criterion Based Outlier Detector

Detailed information about this outlier detection criteria could be found at:
  Lin L, Sherman PD. Cleansing data the Chauvinet way. SESUG Proc. 2007:1–11.

#### Grubbs test Based Outlier Detector

Detailed information about this outlier detection criteria could be found at:
  Grubbs, F. (1969). Procedures for detecting outlying observations in samples. Technometrics 11 (1), 1-21.

#### Dixon test Based Outlier Detector

Detailed information about this outlier detection criteria could be found at:
  1. R. B. Dean and W. J. Dixon (1951) Simplified Statistics for Small Numbers of Observations. Anal. Chem., 1951, 23 (4), 636–638
  2. Rorabacher, David B. (1991) Statistical Treatment for Rejection of Deviant Values: Critical Values of 
  Dixon’s‘ Q’ Parameter and Related Subrange Ratios at the 95% Confidence Level. Analytical Chemistry 63, no. 2 (1991): 139–46.
