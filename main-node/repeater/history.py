class History:
    def __init__(self):
        self.history = {}

    def get(self, point):
        """
        Return list of experiment results in point, if this point exists
        or empty list, if this point does not exist

        :param point: concrete experiment configuration
        :return: list of experiment results in point or empty list
        """
        try:
            return self.history[str(point)]
        except KeyError:
            return []

    def put(self, point, value):
        """
        Store the concrete experiment configuration and its value in the history
        :param point: concrete experiment configuration
        :param value: int, float, list of ints or floats
        """
        try:
            self.history[str(point)].append(value)
        except KeyError:
            self.history[str(point)] = []
            self.history[str(point)].append(value)

    def dump(self, filename):
        """
        Return True, if keys(points) have been written to the filename
        :param filename: name of the file, where keys will write
        :return: True
        """
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
