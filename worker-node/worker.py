
from csv_data.splitter import Splitter

def work():
    data = Splitter("csv_data/Radix-750mio_avg.csv")

    return data.search('2700.0', '32')  