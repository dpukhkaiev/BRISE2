__doc__="""History represents key-value data structure within simple class with a put, get and dump methods for
storing, retrieving and saving history object to the file.  
"""
import logging
import pickle

class History:
    def __init__(self):
        self.history = {}
        self.logger = logging.getLogger(__name__)

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
            return {}

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
        # TODO: Need to update tests for these module.
        try:
            with open(filename, "wb") as f:
                pickle.dump(self.history, f)
            self.logger.info("History saved. Number of written points: %s" % len(self.history))
            return True
        except Exception as e:
            self.logger.error("Failed to write results. Exception: %s" % e, exc_info=True)

    def load(self, filename, flush=False):
        """
        Loads history object from the saved history file.
        :param filename: String. Path to the target file, where history was saved
        :param flush: Bool. Drop all currently saved objects to history before loading, or not.
        :return: Boolean True in case of success.
        """
        # TODO: Need to write tests for these module.
        try:
            with open(filename, 'rb') as f:
                data = pickle.loads(f.read())
                if type(data) != dict:
                    raise TypeError("Incorrect object type(%s) provided in file:%s" % (type(data), filename))
        except IOError or pickle.UnpicklingError or TypeError as error:
            self.logger.error("Unable to load history from the file: %s" % error, exc_info=True)
            return False
        except Exception as e:
            self.logger.error("Unexpected error:%s" %e, exc_info=True)
            return False
        if flush:
            self.history.clear()

        self.history.update(data)
        return True
