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
            'energy': float(result["EN"])
        }
    except Exception as e:
        print("ERROR IN WORKER during performing energy consumption with parameters: %s" %param)

def taskNB(param):
    try:
        data = Splitter("csv_data/"+param['ws_file'])
        # time.sleep(randint(0, 2))
        data.searchNB(str(param['laplace_correction']), str(param['estimation_mode']), 
                      str(param['bandwidth_selection']), str(param['bandwidth']), 
                      str(param['minimum_bandwidth']), str(param['number_of_kernels']),
                      str(param['use_application_grid']), str(param['application_grid_size']))
        result = choice(data.new_data)
        return {
            'PREC_AT_99_REC': result["PREC_AT_99_REC"]
        }
    except Exception as e:
        print("ERROR IN WORKER during performing energy consumption with parameters: %s" %param)

def random_real(param):
    data = Splitter("csv_data/"+param['ws_file'])
    result = data.search(str(param['frequency']), str(param['threads']))
    if result["TIM"]: time.sleep(result["TIM"]/10000) 
    else: time.sleep(2)
    return result

