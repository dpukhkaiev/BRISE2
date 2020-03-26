import csv
import logging

class Splitter:
    data = []
    new_data = []
    param_list = {'app': "app4", 'flac': "cr_audio1.flac", 'wav': "cr_audio1.wav",
                                          'enw8': "enwik8", 'enw9': "enwik9", 'game': "game1",
                                          '01': "01",'02': "02",'03': "03",'04': "04",'05': "05",'06': "06",'07': "07",
                                          '08': "08",'09': "09",'10': "10",'11': "11",'12': "12",'13': "13",'14': "14",
                                          '16': "16",'17': "17",'18': "18",'19': "19",'20': "20",'21': "21",'22': "22", 'sort':"sort", 'encrypt':"encrypt", 'decrypt':"decrypt"}

    def __init__(self, file_name):
        self.logger = logging.getLogger(__name__)
        del self.data[:]
        try:
            with open(file_name, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader: 
                    self.data.append(row)
        except EnvironmentError as error:
            self.logger.error("ERROR in Splitter initialization: %s" % error)

    @staticmethod
    def __str_to_bool(string):
        if string.lower() in ("true"):
            return True
        elif string.lower() in ("false"):
            return False
        else:
            raise ValueError("String \"%s\" is not equal to \"True\" or \"False\"" % string)

    def split(self, param):
        del self.new_data[:] 
        for d in self.data:
            if self.param_list[param] == d["Name"]:
                self.new_data.append(d)

    def search(self, FR, TR):
        del self.new_data[:]
        if self.data:
            for i in self.data:
                if i['FR'] == FR and i['TR'] == TR:
                    self.new_data.append(i)

        return {
            'threads': self.new_data[0]["TR"], 
            'frequency': self.new_data[0]["FR"], 
            'energy': self.new_data[0]["EN"], 
            'time': self.new_data[0]["TIM"]
        } if self.new_data else {"worker": "Error! Incorrect worker config"}

    def searchNB(self, LC, EM, BwS, Bw, MBw, NoK, UAG, AGS):
        del self.new_data[:]
        if self.data:
            for i in self.data:
                if self.__str_to_bool(str(i['laplace_correction'])) == self.__str_to_bool(LC) and \
                        i['estimation_mode'] == EM and i['bandwidth_selection'] == BwS and \
                        i['bandwidth'] == Bw and \
                        i['minimum_bandwidth'] == MBw and \
                        i['number_of_kernels'] == NoK and \
                        self.__str_to_bool(str(i['use_application_grid'])) == self.__str_to_bool(UAG) and \
                        i['application_grid_size'] == AGS:
                    self.new_data.append(i)
        if self.new_data == []: 
            self.new_data.append({})
            self.new_data[0]["PREC_AT_99_REC"] = (str(0.2435))
            return {
                'PREC_AT_99_REC': str(0.2435)
            } 
        return {
            'PREC_AT_99_REC': self.new_data[0]["PREC_AT_99_REC"]
        } if self.new_data else {"worker": "Error! Incorrect worker config"}

    def searchGA(self, file_name):
        del self.new_data[:]
        try:
            with open(file_name, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                last_row = None
                for row in reader:
                    last_row = row
                # selected only last row
                self.new_data.append(last_row)
            return {
                'Solved': self.new_data[0]["Solved"],
                'energy': self.new_data[0]["Obj"],
                'Validity': self.new_data[0]["Validity"],
                'Valid': self.new_data[0]["Valid"],
                'TimeOut': self.new_data[0]["TimeOut"]
            } if self.new_data else {"worker": "Error! Incorect worker config"}
        except EnvironmentError:
            self.logger.error("ERROR occurred in `searchGA` method")

    def searchSA(self, file_name):
        del self.new_data[:]
        try:
            with open(file_name, 'r') as csv_file:
                reader = csv.DictReader(csv_file)
                last_row = None
                for row in reader:
                    last_row = row
                # selected only last row
                self.new_data.append(last_row)
            return {
                'hardScoreImprovement': self.new_data[0]["hardScoreImprovement"],
                'softScoreImprovement': self.new_data[0]["softScoreImprovement"]
            } if self.new_data else {"worker": "Error! Incorrect worker config"}
        except EnvironmentError:
            self.logger.error("ERROR occurred in `searchSA` method")


    def make_csv(self, name, data_type):
        csv_name = "tmp/" + name[:-4] + "_" + data_type + ".csv"
        with open(csv_name, 'wb') as result:
            fieldnames = self.data[0].keys()
            writer = csv.DictWriter(result, dialect='excel', fieldnames= fieldnames)
            writer.writeheader()
            for d in self.data:
                writer.writerow(d)
        return csv_name
