import logging
class History:
    def __init__(self):
        self.history = {}

    def get(self, point):
        try:
            return  self.history[str(point)]
        except KeyError:
            return {}

    def put(self, point, values):
        try:
            self.history[str(point)].append(values)
        except KeyError:
            self.history[str(point)] = []
            self.history[str(point)].append(values)

    def dump(self, filename):

        try:
            lines = 0
            with open(filename, "w") as f:
                for key in self.history.keys():
                    f.write(key)
                    lines += 1
            print("History dumped. Number of written points: %s" % lines)
            return True
        except Exception as e:
            print("Failed to write results. Exception: %s" % e)
