from random import randint
import time

from csv_data.splitter import Splitter

def work(fr, tr):
    data = Splitter("csv_data/Radix-750mio_avg.csv")

    return data.search(str(fr), str(tr))  

def random_1(param):
    data = Splitter("csv_data/Radix-750mio_avg.csv")
    time.sleep(randint(3, 7))
    return data.search(str(param['fr']), str(param['tr']))  

def random_2(param):
    data = Splitter("csv_data/Radix-750mio_avg.csv")
    time.sleep(randint(3, 6))
    return data.search(str(param['fr']), str(param['tr']))  
    