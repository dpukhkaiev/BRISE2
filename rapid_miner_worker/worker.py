from random import randint, choice
import time

from csv_data.splitter import Splitter

def work(param):
    data = Splitter("csv_data/Radix-750mio_avg.csv")
    return data.search(str(param['frequency']), str(param['threads']))  

def random_1(param):
    data = Splitter("csv_data/"+param['ws_file'])
    time.sleep(randint(1, 3))
    return data.search(str(param['frequency']), str(param['threads']))


def random_2(param):
    data = Splitter("csv_data/"+param['ws_file'])
    time.sleep(randint(1, 5))
    return data.search(str(param['frequency']), str(param['threads']))

def energy_consumption(param):
    try:
        data = Splitter("csv_data/"+param['ws_file'])
        # time.sleep(randint(0, 2))
        data.search(str(param['frequency']), str(param['threads']))
        result = choice(data.new_data)
        return {
            'threads': result["TR"],
            'frequency': result["FR"],
            'energy': result["EN"],
            'time': result["TIM"]
        }
    except Exception as e:
        print("ERROR IN WORKER during performing energy consumption with parameters: %s" %param)

def naive_bayes_process(param):
    # change hyperparameters of RapidMiner process
    import xml.etree.ElementTree
    process = xml.etree.ElementTree.parse('./swc-data//processes/MA_EXR_1_EX_1_NB_INV.rmp')
    for atype in process.findall('operator/process/operator/process/operator'):
        if(atype.get('name') == "NAIVE_BAYES_KERNEL"):
            for parameter in atype:
                if(param.get(parameter.get('key'), 0) != 0):
                    print("str(parameter.get('key')): " + str(parameter.get('key')))
                    print(str(param[parameter.get('key')]))
                    parameter.set('value', str(param[parameter.get('key')]))
            break
    process.write('./swc-data//processes/MA_EXR_1_EX_1_NB_INV.rmp')

    # execut process
    import subprocess
    import os
    print("start RapidMiner")
    pr = os.system("./rapidminer-studio/scripts/rapidminer-batch.sh //swc-data/processes/MA_EXR_1_EX_1_NB_INV")
    print("end process: " + str(pr))
    time.sleep(5)
    print("this is shit!!!")

def random_real(param):
    data = Splitter("csv_data/"+param['ws_file'])
    result = data.search(str(param['frequency']), str(param['threads']))
    if result["TIM"]: time.sleep(result["TIM"]/10000) 
    else: time.sleep(2)
    return result

if __name__ == "__main__":
    param = {'ws_file': '', 'laplace_correction': True, 'use_application_grid': True, 'estimation_mode': 'full', 'bandwidth_selection': 'heuristic'}
    naive_bayes_process(param)
