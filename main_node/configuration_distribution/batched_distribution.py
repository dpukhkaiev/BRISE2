import json
import threading

from configuration_distribution.distribution_abs import AbstractDistribution
from tools.rabbitmq_common_tools import publish


class BatchedDistribution(AbstractDistribution):

    def __init__(self, config: dict):

        super().__init__(config)

        try:
            self._batch_size = int(config["BatchedDistribution"]["BatchSize"])
            self.logger.info(f"Batched Distribution initialized with batch size: {self._batch_size}")

        except KeyError:
            self.logger.error("Description missing 'BatchSize'!")
            raise ValueError("Batched Distribution requires 'BatchSize' in description.")

        self._first_it = True
        self._barrier = None

        self._first_it_lock = threading.Lock()
        self._barrier_lock = threading.Lock()

    def handle_configuration_distribution(self, experiment_id, body):

        self.logger.info(f"Waiting for all workers to be synchronized")

        # ? wait until every worker has came to wait()
        if self._barrier:
            self.logger.info(f'Workers currently waiting {str(self._barrier.n_waiting + 1)}')
            self._barrier.wait()

        self.logger.info(f"Worker synchronized")

        publish(exchange='get_new_configuration_exchange',
                routing_key=experiment_id,
                body=body)

    def dispatch(self, experiment_id, body):

        if self.first_it(experiment_id):
            return

        # * Check for existing or broken barrier and create one
        with self._barrier_lock:
            if self._barrier is None:
                self.logger.info(f"Creating new barrier with size {self._batch_size}")
                self._barrier = threading.Barrier(self._batch_size)

        # * Forward the call to a separate thread.
        # * In case of blocking, the event thread stays unblocked
        threading.Thread(target=self.handle_configuration_distribution, args=(experiment_id, body), daemon=True).start()

    def first_it(self, experiment_id):

        # ! setting of the first wave of configurations is important
        with self._first_it_lock:
            if self._first_it:

                self.logger.info(f"Proposing the first {self._batch_size} configurations")
                dictionary_dump = {"worker_capacity": self._batch_size}
                body = json.dumps(dictionary_dump)

                publish(exchange='get_new_configuration_exchange',
                        routing_key=experiment_id,
                        body=body)

                self._first_it = False
                return True
        return False