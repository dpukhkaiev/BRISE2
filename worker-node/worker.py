from random import randint
import time

from csv_data.splitter import Splitter

def work(fr, tr):
    data = Splitter("csv_data/Radix-750mio_avg.csv")

    return data.search(str(fr), str(tr))  

def random_1(param):
    data = Splitter("csv_data/Radix-750mio_avg.csv")
    time.sleep(randint(1, 3))
    return data.search(str(param['frequency']), str(param['threads']))  

def random_2(param):
    data = Splitter("csv_data/Radix-750mio_avg.csv")
    time.sleep(randint(1, 3))
    return data.search(str(param['frequency']), str(param['threads']))  
    