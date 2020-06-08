import pytest
from tools.initial_config import load_experiment_setup

@pytest.fixture(scope='function')
def get_sample():

    configurations_sample = [
        {"Params" : [2900.0, 32], "Tasks" : 10, "Outliers" : 0, "Avg.result" : [252.49864000000002], "STD" : [141.10616692433535]}, 
        {"Params" : [2700.0, 2], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [1586.7649999999999], "STD" : [94.80499999999995]},
        {"Params" : [1700.0, 16], "Tasks" : 3, "Outliers" : 1, "Avg.result" : [563.947], "STD" : [1.8780000000000427]}, 
        {"Params" : [1900.0, 4], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [1072.46], "STD" : [0.0]}, 
        {"Params" : [2400.0, 1], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [3311.375], "STD" : [45.965000000000146]}, 
        {"Params" : [2200.0, 8], "Tasks" : 10, "Outliers" : 0, "Avg.result" : [703.0388], "STD" : [141.51704243433014]}, 
        {"Params" : [1400.0, 8], "Tasks" : 3, "Outliers" : 1, "Avg.result" : [517.611], "STD" : [0.0]}, 
        {"Params" : [1600.0, 2], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [2056.1000000000004], "STD" : [19.970000000000027]}, 
        {"Params" : [2900.0, 1], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [3011.5950000000003], "STD" : [34.93500000000017]}, 
        {"Params" : [2500.0, 16], "Tasks" : 6, "Outliers" : 1, "Avg.result" : [512.7272], "STD" : [29.830272552559737]}, 
        {"Params" : [2901.0, 1], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [3095.75], "STD" : [37.61999999999989]}, 
        {"Params" : [2901.0, 2], "Tasks" : 5, "Outliers" : 1, "Avg.result" : [1186.9915], "STD" : [233.11639345346353]}, 
        {"Params" : [2000.0, 8], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [712.4155000000001], "STD" : [1.0564999999999714]}, 
        {"Params" : [2800.0, 1], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [2578.13], "STD" : [43.690000000000055]}, 
        {"Params" : [1800.0, 2], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [1868.22], "STD" : [49.92000000000007]}, 
        {"Params" : [2300.0, 4], "Tasks" : 3, "Outliers" : 0, "Avg.result" : [1071.0516666666665], "STD" : [99.77869798820903]}, 
        {"Params" : [2901.0, 4], "Tasks" : 3, "Outliers" : 0, "Avg.result" : [1076.4], "STD" : [63.59265104292056]}, 
        {"Params" : [2800.0, 16], "Tasks" : 10, "Outliers" : 1, "Avg.result" : [422.6666666666667], "STD" : [72.33458598454514]}, 
        {"Params" : [2900.0, 2], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [1419.43], "STD" : [0.0]}, 
        {"Params" : [2901.0, 32], "Tasks" : 10, "Outliers" : 0, "Avg.result" : [272.29141], "STD" : [106.3763995179988]}, 
        {"Params" : [1300.0, 32], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [381.7025], "STD" : [0.6394999999999982]}, 
        {"Params" : [1300.0, 4], "Tasks" : 5, "Outliers" : 0, "Avg.result" : [1362.8452000000002], "STD" : [356.4619780287373]}, 
        {"Params" : [2300.0, 32], "Tasks" : 10, "Outliers" : 0, "Avg.result" : [288.25816000000003], "STD" : [100.67858002490102]}, 
        {"Params" : [2800.0, 2], "Tasks" : 4, "Outliers" : 0, "Avg.result" : [1306.775], "STD" : [250.02962599460085]}, 
        {"Params" : [1200.0, 32], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [451.882], "STD" : [0.0]}, 
        {"Params" : [1200.0, 16], "Tasks" : 7, "Outliers" : 0, "Avg.result" : [558.8384285714285], "STD" : [55.907116781464666]}, 
        {"Params" : [1800.0, 16], "Tasks" : 10, "Outliers" : 0, "Avg.result" : [391.95238], "STD" : [144.81335122363407]}, 
        {"Params" : [1200.0, 4], "Tasks" : 3, "Outliers" : 0, "Avg.result" : [1718.4566666666667], "STD" : [267.04512257086617]}, 
        {"Params" : [1200.0, 8], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [1006.7529999999999], "STD" : [8.896999999999991]}, 
        {"Params" : [1300.0, 16], "Tasks" : 10, "Outliers" : 1, "Avg.result" : [539.8192222222223], "STD" : [71.44443433385104]}, 
        {"Params" : [1200.0, 1], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [4909.805], "STD" : [2.644999999999982]}, 
        {"Params" : [2000.0, 1], "Tasks" : 3, "Outliers" : 0, "Avg.result" : [3242.86], "STD" : [359.8294073585427]}, 
        {"Params" : [1200.0, 2], "Tasks" : 2, "Outliers" : 0, "Avg.result" : [2540.97], "STD" : [14.5]}, 
        {"Params" : [2901.0, 8], "Tasks" : 3, "Outliers" : 1, "Avg.result" : [767.263], "STD" : [0.0]}, 
        {"Params" : [2500.0, 4], "Tasks" : 5, "Outliers" : 1, "Avg.result" : [1188.555], "STD" : [87.20003598049715]}, 
        {"Params" : [1600.0, 32], "Tasks" : 4, "Outliers" : 1, "Avg.result" : [413.7816666666667], "STD" : [7.06894194503127]}, 
        {"Params" : [2901.0, 16], "Tasks" : 10, "Outliers" : 1, "Avg.result" : [168.70434444444444], "STD" : [83.12452132603514]}]

    tasks_sample = [{'result': {'energy': 223.3292}, 'worker': 'alpha', 'task id': 'e699ce2aaad443f88f258ae543262ea2', 'ResultValidityCheckMark': 'OK'}, 
        {'result': {'energy': 226.294}, 'worker': 'alpha', 'task id': '19e1bb7007854fc1a6a827cab28ede3f', 'ResultValidityCheckMark': 'OK'}, 
        {'result': {'energy': 392.655}, 'worker': 'alpha', 'task id': '715f2e8628374a2d8cbf794bbafb1261', 'ResultValidityCheckMark': 'OK'}, 
        {'result': {'energy': 309.047}, 'worker': 'alpha', 'task id': '9ce08308fbff411cb7cc1655ad43effe', 'ResultValidityCheckMark': 'OK'}, 
        {'result': {'energy': 240.834}, 'worker': 'alpha', 'task id': '62e90c3e1014419a950b4c4bcc6cfe80', 'ResultValidityCheckMark': 'OK'}, 
        {'result': {'energy': 426.294}, 'worker': 'alpha', 'task id': '83cfbe0ba6c143398444bcc3d54760ed', 'ResultValidityCheckMark': 'OK'}, 
        {'result': {'energy': 201.645}, 'worker': 'alpha', 'task id': 'd33175099efb4d23a6f116f5e79cb339', 'ResultValidityCheckMark': 'OK'}, 
        {'result': {'energy': 392.655}, 'worker': 'alpha', 'task id': '63e935209f2648a3bb0e43a6ea67ac34', 'ResultValidityCheckMark': 'OK'}, 
        {'result': {'energy': 426.294}, 'worker': 'alpha', 'task id': '68242f8c94ac4f849ba848785ced5ad2', 'ResultValidityCheckMark': 'OK'}, 
        {'result': {'energy': 201.645}, 'worker': 'alpha', 'task id': '315d0b8bf84f45018c14c4853baa321d', 'ResultValidityCheckMark': 'OK'}]

    experiment_description, search_space = load_experiment_setup("./Resources/EnergyExperiment.json")
    yield (configurations_sample, tasks_sample, experiment_description, search_space)
