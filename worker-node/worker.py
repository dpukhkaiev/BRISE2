
from csv_data.splitter import Splitter

def work(fr, tr):
    data = Splitter("csv_data/Radix-750mio_avg.csv")

    return data.search(str(fr), str(tr))  