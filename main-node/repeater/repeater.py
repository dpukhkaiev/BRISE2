import logging

from tools.front_API import API
from tools.reflective_class_import import reflective_class_import
from core_entities.configuration import Configuration
from core_entities.experiment import Experiment


class Repeater:
    def __init__(self, worker_service_client, experiment):

        self.worker_service_client = worker_service_client
        self.performed_measurements = 0
        self.repeater_parameters = experiment.description["Repeater"]["Parameters"]

        self.logger = logging.getLogger(__name__)

        self._type = None
        self.set_type("Default")  # Default Configuration will be measured precisely with Default Repeater Type.

    def evaluation_by_type(self, current_configuration: Configuration, experiment: Experiment):
        """
        Forwards a call to specific Repeater Type to evaluate if Configuration was measured precisely.
        :param current_configuration: instance of Configuration class.
        :param experiment: instance of 'experiment' is required for model-awareness.
        :return: int Number of measurments of Configuration which need to be performed 
        """

        if self._type is None:
            raise TypeError("Repeater evaluation Type was not selected!")
        else:
            return self._type.evaluate(current_configuration=current_configuration, experiment=experiment)

    def set_type(self, repeater_type: str):
        """
            This method change current Type of Repeater.
        :param repeater_type: String.
                The name of Repeater Type with desired evaluation function for repeater.
                Possible values - "Default", "Student Deviation".
                "Default" - adds fixed number of Tasks to each Configuration, no evaluation performed.
                "Student deviation" - adds Tasks until result of Configuration measurement reaches appropriate accuracy,
                the quality of each configuration (how it close to currently best found Configuration) and deviation of
                each experiment are taken into account.
        :return: None.
        """
        evaluation_class = reflective_class_import(class_name=repeater_type, folder_path="repeater")
        self._type = evaluation_class(self.repeater_parameters)
    
    def measure_configurations(self, configurations: list, experiment: Experiment):
        """
        Evaluates the Target System using specific Configuration while results of Evaluation will not be precise.
        :param configurations: list of Configurations that are needed to be measured.
        :param experiment: instance of 'experiment' is required for model-awareness.
        :return: list of Configurations that were evaluated
        """
        # Removing previous measurements
        current_measurement = {}
        # Creating holders for current measurements
        for configuration in configurations:
            # Evaluating each Configuration in configurations list
            needed_tasks_count = self.evaluation_by_type(configuration, experiment)
            current_measurement[str(configuration.get_parameters())] = {'parameters': configuration.get_parameters(),
                                                                        'needed_tasks_count' : needed_tasks_count,
                                                                        'Finished': False}
            
            if needed_tasks_count == 0:
                current_measurement[str(configuration.get_parameters())]['Finished'] = True
                current_measurement[str(configuration.get_parameters())]['Results'] = configuration.get_average_result()

        # Continue to feed with a new Tasks while not passing the evaluation.
        while True:

            # Selecting only that configurations that were not finished.
            tasks_to_send = []
            for point in current_measurement.keys():
                if not current_measurement[point]['Finished']:
                    for i in range(current_measurement[point]['needed_tasks_count']):
                        tasks_to_send.append(current_measurement[point]['parameters'])
                        self.performed_measurements += 1

            if not tasks_to_send:
                return configurations

            # Send this configurations to Worker service
            results = self.worker_service_client.work(tasks_to_send)

            # Sending data to API and adding Tasks to Configuration
            for parameters, result in zip(tasks_to_send, results):
                for config in configurations:
                    if config.get_parameters() == parameters:
                        config.add_tasks(parameters, result)

                API().send('new', 'task', configurations=[parameters], results=[result])
            
            # Evaluating each Configuration in configurations list
            for configuration in configurations:
                needed_tasks_count = self.evaluation_by_type(configuration, experiment)
                current_measurement[str(configuration.get_parameters())]['needed_tasks_count'] = needed_tasks_count
                if needed_tasks_count  == 0:
                    temp_msg = ("Configuration measured: %s" % configuration)
                    self.logger.info(temp_msg)
                    API().send('log', 'info', message=temp_msg)
                    current_measurement[str(configuration.get_parameters())]['Finished'] = True
                    current_measurement[str(configuration.get_parameters())]['Results'] = configuration.get_average_result()
