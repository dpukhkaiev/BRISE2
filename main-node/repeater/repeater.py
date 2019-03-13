import logging

from tools.front_API import API


class Repeater:
    def __init__(self, worker_service_client, experiment):

        self.worker_service_client = worker_service_client
        self.performed_measurements = 0
        self.repeater_configuration = experiment.description["RepeaterConfiguration"]

        self.logger = logging.getLogger(__name__)

        self.task_id = 0       # should be deleted, receive from worker_service_client
        self.worker = "alpha"  # should be deleted, receive from worker_service_client

        # Instance of Judge class providing strategy for making `verdict`s:
        # "should we continue with new Tasks for particular Configurations or not".
        self._judge = None
        self.set_judge("default")  # Default Configuration will be measured precisely with default Judge.

    def decision_function(self, *args, **params):

        if self._judge is None:
            raise TypeError("Repeater decision function was not selected!")
        else:
            return self._judge.verdict(*args, **params)

    def set_judge(self, judge_name: str):
        """
            This method change current decision function of repeater provided by judge at runtime.
        :param judge_name: String.
                The name of judge with desired decision function for repeater.
                Possible values - "default", "student_deviation".
                "default" - adds fixed number of Tasks to each Configuration, no evaluation performed.
                "student_deviation" - adds Tasks until result of Configuration measurement reaches appropriate accuracy,
                the quality of each configuration (how it close to currently best found Configuration) and deviation of
                each experiment are taken into account.
        :return: None.
        """
        # TODO: Importing using package name in experiment description file instead this if-else construction.
        if judge_name == "default":
            from repeater.default_judge import DefaultJudge
            self._judge = DefaultJudge(self.repeater_configuration)
        elif judge_name == "student_deviation":
            from repeater.student_judge import StudentJudge
            self._judge = StudentJudge(self.repeater_configuration)
        else:
            self.logger.error("Invalid repeater type provided: %s!" % judge_name)
            raise KeyError("Invalid repeater type provided: %s!" % judge_name)

    def measure_configurations(self, configurations, **params):
        """
        :param configurations: list of instances of Configuration class

        """
        # Removing previous measurements
        current_measurement = {}
        current_measurement_finished = False
        # Creating holders for current measurements
        for configuration in configurations:
            # Evaluating decision function for each configuration in configurations list
            current_measurement[str(configuration.get_parameters())] = {'data': configuration.get_parameters(),
                                                                        'Finished': False}
            result = self.decision_function(configuration, **params)
            if result:
                current_measurement[str(configuration.get_parameters())]['Finished'] = True
                current_measurement[str(configuration.get_parameters())]['Results'] = result

        # Continue to make measurements while decision function will not terminate it.
        while not current_measurement_finished:

            # Selecting only that configurations that were not finished.
            tasks_to_send = []
            for point in current_measurement.keys():
                if not current_measurement[point]['Finished']:
                    tasks_to_send.append(current_measurement[point]['data'])
                    self.performed_measurements += 1

            if not tasks_to_send:
                return None

            # Send this configurations to Worker service
            results = self.worker_service_client.work(tasks_to_send)

            # Sending data to API
            for parameters, result in zip(tasks_to_send, results):
                for config in configurations:
                    if config.get_parameters() == parameters:
                        config.add_tasks(parameters, str(self.task_id), result, self.worker)

                API().send('new', 'task', configurations=[parameters], results=[result])
                self.task_id += 1

            # Evaluating decision function for each configuration
            for task in tasks_to_send:
                for config in configurations:
                    if task == config.get_parameters():
                        result = self.decision_function(config, **params)
                        if result:
                            temp_msg = ("Configuration measured: %s" % config)
                            self.logger.info(temp_msg)
                            API().send('log', 'info', message=temp_msg)
                            current_measurement[str(task)]['Finished'] = True
                            current_measurement[str(task)]['Results'] = result
