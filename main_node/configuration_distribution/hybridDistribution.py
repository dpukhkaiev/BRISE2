from configuration_distribution.distribution_abs import AbstractDistribution
from tools.rabbitmq_common_tools import RabbitMQConnection, publish

import threading
import logging
from collections import deque
import json
import time
import numpy as np

class EventGate:
    """
    Holds the shared synchronization state (Event, Timer).
    This is a simple, pure barrier.
    """
    def __init__(self, _batch_size, _timeout, cleanup_callback):

        self.logger = logging.getLogger(self.__class__.__name__)

        self._batch_size = _batch_size
        self._timeout = _timeout
        self.cleanup_callback = cleanup_callback

        # gate initialization
        self.gate = threading.Event()
        self.arrival_count = 0
        self.count_lock = threading.Lock()

        # idle timer logic
        self.stats_lock = threading.Lock()
        self.wait_times = []
        self.expected_reporters = 0
        self.trigger_result = "unknown"
        self.start_time = time.time()

        # timeout logic
        self.trigger_lock = threading.Lock()
        self.triggered = False
        self.timer = threading.Timer(self._timeout, self._trigger_by_timeout)
        self.timer.start()

        # single-publisher logic: exactly one released worker per wave publishes
        # the next selection request (see wait_at_gate / multi-point proposal).
        self.publish_lock = threading.Lock()
        self.has_published = False
        # self.logger.info(f"New gate created with batch_size {self._batch_size} and timeout {self._timeout}s")

    def _trigger_release(self, result: str):
        """Internal: Opens the gate."""
        if not self.triggered:
            self.triggered = True

            self.trigger_result = result
            self.expected_reporters = self.arrival_count
            self.arrival_count = 0

            self.gate.set()

    def _trigger_by_timeout(self):
        """Called by the timer."""
        with self.trigger_lock:
            if not self.triggered:
                self.logger.warning(f"--- TIMEOUT! Releasing {self.arrival_count} threads. ---")
                self._trigger_release(result="timeout")

    def _trigger_by_completion(self):
        """Called by the last worker to arrive."""
        with self.trigger_lock:
            if not self.triggered:
                self.logger.info(f"--- All {self._batch_size} Workers arrived!. Releasing. ---")
                self.timer.cancel()
                self._trigger_release(result="completion")

    def _aggregate_and_cleanup(self):
        """
        Called by the last worker to report.
        Aggregates stats and triggers the cleanup.
        """
        if not self.wait_times:
            # edge case where 0 workers arrived on timeout
            stats = {
                "result": self.trigger_result,
                "avg_wait_time": 0,
                "max_wait_time": 0,
                "total_time_taken": time.time() - self.start_time
            }
        else:
            avg_wait = np.mean(self.wait_times)
            max_wait = np.max(self.wait_times)
            
            stats = {
                "result": self.trigger_result,
                "avg_wait_time": avg_wait,
                "max_wait_time": max_wait,
                "total_time_taken": time.time() - self.start_time
            }

        if self.cleanup_callback:
            self.cleanup_callback(stats)

    def wait_at_gate(self):
        """
        The main barrier logic. The worker thread just waits here.

        :return: True for exactly one released worker per wave (the designated
                 publisher), False for the rest. The caller publishes a single
                 next-wave selection request only when this is True.
        """
        # 1. Count arrival
        with self.count_lock:
            self.arrival_count += 1

        self.logger.info(f'Workers currently waiting {str(self.arrival_count)}')

        # 2. Check if its the last one
        if self.arrival_count == self._batch_size:
            self._trigger_by_completion()

        # 3. Wait until the gate is opened
        wait_start_time = time.time()
        self.gate.wait()
        wait_time = time.time() - wait_start_time

        # Designate a single publisher for this wave: the first worker to reach
        # this point after the gate opens. Avoids every released worker triggering
        # its own single-point selection.
        with self.publish_lock:
            should_publish = not self.has_published
            self.has_published = True

        is_last_reporter = False

        with self.stats_lock:
            self.wait_times.append(wait_time)

            # Check if the last worker was released
            if len(self.wait_times) == self.expected_reporters:
                is_last_reporter = True

        if is_last_reporter:
            self._aggregate_and_cleanup()

        return should_publish

class HybridDistribution(AbstractDistribution):
    """
    This class acts as a central coordinator, providing a hybrid
    (timeout-based) synchronization barrier for workers.
    """

    def __init__(self, config: dict):

        super().__init__(config)

        try:
            self._batch_size = int(config["batchSize"]["Int"])

        except KeyError:
            self.logger.error("Description missing 'batchSize'!")
            raise ValueError("Hybrid Distribution requires 'batchSize' in description.")

        self._gate = None
        self.gate_lock = threading.Lock()

        self._first_it = True
        self._first_it_lock = threading.Lock()

        # `TimeoutInSeconds` is the initial per-wave release timeout, used until
        # enough worker evaluation times have been collected to adapt it
        # (see _calculate_next_timeout). Optional; defaults to 5 seconds.
        try:
            self._initial_timeout = float(config["TimeoutInSeconds"]["Int"])
        except (KeyError, TypeError, ValueError):
            self.logger.info("No valid 'TimeoutInSeconds' in description; defaulting to 5 seconds.")
            self._initial_timeout = 5.0

        self._number_of_workers = 0
        self._evaluation_times = []

    def _cleanup_gate(self, stats: dict):
            """Internal: Callback to destroy the gate."""
            with self.gate_lock:
                self._gate = None

    def _calculate_next_timeout(self):
        # self.logger.info(f"Evaluation Times: {self._evaluation_times}")

        TIMEOUT_BUFFER_FACTOR = 0.5
        MIN_TIMEOUT = 1
        
        workers = self._number_of_workers  # 3
        
        # * Focus on the last full proposal's worth of data
        # * Assumption your EventGate releases a proposal of 5 results at a time:
        PROPOSAL_SIZE = 5 
        
        if len(self._evaluation_times) < PROPOSAL_SIZE:
            # not enough data to adapt yet -> use the configured initial timeout
            return self._initial_timeout

        last_proposal_times = self._evaluation_times[-PROPOSAL_SIZE:]
        
        # ? Divide the proposal times into rounds
        max_round_times = []
        
        for i in range(0, len(last_proposal_times), workers):
            round_times = last_proposal_times[i:i + workers]
            if round_times:
                max_round_times.append(max(round_times))
                
        # ? sum the max times of all rounds in the last proposal
        proposal_time = sum(max_round_times)

        # self.logger.info(f"Max eval times per round in last proposal: {max_round_times}")
        
        next_timeout = proposal_time * (1 + TIMEOUT_BUFFER_FACTOR)

        # self.logger.info(f"Calculated next timeout: {next_timeout}s")
    
        return max(next_timeout, MIN_TIMEOUT)
           
    def _get_or_create_gate(self):
        """Thread-safe method to get the current gate or create a new one."""
        with self.gate_lock:
            # If the gate doesn't exist, create one
            # This happens when the first worker of a new batch arrives
            if self._gate is None:
                _current_timeout = self._calculate_next_timeout()
                self.logger.info(f"Creating new EventGate with batch size {self._batch_size} and timeout {_current_timeout}s")
                self._gate = EventGate(self._batch_size, _current_timeout, self._cleanup_gate)

            return self._gate

    def handle_configuration_distribution(self, experiment_id, body):
        """
        This method finds the correct
        barrier and blocks the worker thread until a Release Event occurs.
        """

        gate = self._get_or_create_gate()

        should_publish = gate.wait_at_gate()

        # Emit exactly ONE request per release wave carrying the full batch size,
        # so a single surrogate build proposes `batchSize` distinct points (true
        # multi-point proposal) instead of every released worker proposing one.
        if should_publish:
            wave_body = json.dumps({"worker_capacity": self._batch_size})
            publish(exchange='get_new_configuration_exchange',
                    routing_key=experiment_id,
                    body=wave_body)

    def dispatch(self, experiment_id, body):

        if body:
            input_data = json.loads(body)
            self._evaluation_times.append(input_data.get('repetition_time'))
            self._number_of_workers = input_data.get('number_of_workers')
            # self.logger.info(f"meta: {self._evaluation_times}, {self._number_of_workers}")

        if self.first_it(experiment_id):
            return
        
        threading.Thread(target=self.handle_configuration_distribution,args=(experiment_id, body),daemon=True).start()

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