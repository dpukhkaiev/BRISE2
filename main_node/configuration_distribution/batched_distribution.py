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
        barrier = self._barrier
        release_index = None
        if barrier:
            self.logger.info(f'Workers currently waiting {str(barrier.n_waiting + 1)}')
            try:
                release_index = barrier.wait()
            except threading.BrokenBarrierError:
                # The wave can never release on its own (a worker died or the
                # barrier was aborted): start the next wave from a fresh barrier.
                self.logger.warning("Barrier broke before the batch completed; "
                                    "discarding it and recovering for the next wave.")
                self._discard_broken_barrier(barrier)
                return

        self.logger.info(f"Worker synchronized")

        # One request per released wave, carrying the full batch size, so a single
        # surrogate build proposes BatchSize points (multi-point proposal).
        # Barrier.wait() hands every released thread a unique index; index 0 publishes.
        if release_index in (None, 0):
            publish(exchange='get_new_configuration_exchange',
                    routing_key=experiment_id,
                    body=json.dumps({"worker_capacity": self._batch_size}))

    def _discard_broken_barrier(self, barrier):
        """Drop a broken barrier, unless a fresh one has already replaced it."""
        with self._barrier_lock:
            if self._barrier is barrier:
                self._barrier = None

    def dispatch(self, experiment_id, body):

        if self.first_it(experiment_id):
            return

        # * Check for a missing or broken barrier and create a fresh one
        with self._barrier_lock:
            if self._barrier is None or self._barrier.broken:
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