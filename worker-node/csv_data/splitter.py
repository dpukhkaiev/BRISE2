import csv

class Splitter:
    data = []
    new_data = []
    param_list = {'app': "app4", 'flac': "cr_audio1.flac", 'wav': "cr_audio1.wav",
                                          'enw8': "enwik8", 'enw9': "enwik9", 'game': "game1",
                                          '01': "01",'02': "02",'03': "03",'04': "04",'05': "05",'06': "06",'07': "07",
                                          '08': "08",'09': "09",'10': "10",'11': "11",'12': "12",'13': "13",'14': "14",
                                          '16': "16",'17': "17",'18': "18",'19': "19",'20': "20",'21': "21",'22': "22", 'sort':"sort", 'encrypt':"encrypt", 'decrypt':"decrypt"}

    def __init__(self, file_name):
        del self.data[:]
        with open(file_name, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                self.data.append(row)

    def split(self, param):
        del self.new_data[:]
        for d in self.data:
            if self.param_list[param] == d["Name"]:
                self.new_data.append(d)

    def search(self, FR, TR):
        del self.new_data[:]
        for i in self.data:
            if i['FR'] == FR and i['TR'] == TR:
                self.new_data.append(i)
        return self.new_data
                

    def make_csv(self, name, data_type):
        csv_name = "tmp/" + name[:-4] + "_" + data_type + ".csv"
        with open(csv_name, 'wb') as result:
            fieldnames = self.data[0].keys()
            writer = csv.DictWriter(result, dialect='excel', fieldnames= fieldnames)
            writer.writeheader()
            for d in self.data:
                writer.writerow(d)
        return csv_name