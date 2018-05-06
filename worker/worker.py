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

def random_real(param):
    data = Splitter("csv_data/"+param['ws_file'])
    result = data.search(str(param['frequency']), str(param['threads']))
    if result["TIM"]: time.sleep(result["TIM"]/10000) 
    else: time.sleep(2)
    return result

