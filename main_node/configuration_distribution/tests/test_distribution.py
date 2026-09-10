import logging
import json
import threading
from collections import deque
import pytest
from unittest.mock import patch, MagicMock, call

from configuration_distribution.configuration_distribution_orchestrator import ConfigurationDistributionOrchestrator
from configuration_distribution.batched_distribution import BatchedDistribution
from configuration_distribution.hybrid_distribution import HybridDistribution, EventGate
from configuration_distribution.asynchronous_distribution import AsynchronousDistribution

# disable logging
logging.disable(logging.CRITICAL)

class TestConfigurationDistributionOrchestrator:

    @pytest.fixture(autouse=True)
    def setup(self, get_distribution_experiment):
        """Set up a new orchestrator instance for each test."""
        self.orchestrator = ConfigurationDistributionOrchestrator()
        self.get_distribution_experiment = get_distribution_experiment

    # Test 1: Using EnergyExperiment_Adistr.json config
    @patch('configuration_distribution.configuration_distribution_orchestrator.reflective_class_import')
    def test_get_distribution_asynchronous(self, mock_reflective_import):
        """
        Tests the AsynchronousDistribution config from EnergyExperiment_Adistr.json
        """
        # --- Arrange ---
        mock_distribution_instance = MagicMock(spec=AsynchronousDistribution)
        mock_distribution_class = MagicMock(return_value=mock_distribution_instance)
        mock_reflective_import.return_value = mock_distribution_class

        # This is the config from EnergyExperiment_Adistr.json
        experiment_config, _ = self.get_distribution_experiment("A")
        expected_constructor_arg = experiment_config["DistributionMode"]
        expected_distribution_type = expected_constructor_arg["AsynchronousDistribution"]["Type"]

        # --- Act ---
        result = self.orchestrator.get_distribution(experiment_config["DistributionMode"])

        # --- Assert ---
        mock_reflective_import.assert_called_once_with(
            class_name=expected_distribution_type,
            folder_path="configuration_distribution"
        )
        mock_distribution_class.assert_called_once_with(expected_constructor_arg)
        assert result == mock_distribution_instance

    # Test 2: Using EnergyExperiment_Bdistr.json config
    @patch('configuration_distribution.configuration_distribution_orchestrator.reflective_class_import')
    def test_get_distribution_batched(self, mock_reflective_import):
        """
        Tests the BatchedDistribution config from EnergyExperiment_Bdistr.json
        """
        # --- Arrange ---
        mock_distribution_instance = MagicMock(spec=BatchedDistribution)
        mock_distribution_class = MagicMock(return_value=mock_distribution_instance)
        mock_reflective_import.return_value = mock_distribution_class

        # This is the config from EnergyExperiment_Bdistr.json
        experiment_config, _ = self.get_distribution_experiment("B")
        expected_constructor_arg = experiment_config["DistributionMode"]
        expected_distribution_type = expected_constructor_arg["BatchedDistribution"]["Type"]

        # --- Act ---
        result = self.orchestrator.get_distribution(experiment_config["DistributionMode"])

        # --- Assert ---
        mock_reflective_import.assert_called_once_with(
            class_name=expected_distribution_type,
            folder_path="configuration_distribution"
        )
        mock_distribution_class.assert_called_once_with(expected_constructor_arg)
        assert result == mock_distribution_instance

    # Test 3: Using EnergyExperiment_Hdistr.json config
    @patch('configuration_distribution.configuration_distribution_orchestrator.reflective_class_import')
    def test_get_distribution_hybrid(self, mock_reflective_import):
        """
        Tests the HybridDistribution config from EnergyExperiment_Hdistr.json
        """
        # --- Arrange ---
        mock_distribution_instance = MagicMock(spec=HybridDistribution)
        mock_distribution_class = MagicMock(return_value=mock_distribution_instance)
        mock_reflective_import.return_value = mock_distribution_class

        # This is the config from EnergyExperiment_Hdistr.json
        experiment_config, _ = self.get_distribution_experiment("H")
        expected_constructor_arg = experiment_config["DistributionMode"]
        expected_distribution_type = expected_constructor_arg["HybridDistribution"]["Type"]

        # --- Act ---
        result = self.orchestrator.get_distribution(experiment_config["DistributionMode"])

        # --- Assert ---
        mock_reflective_import.assert_called_once_with(
            class_name=expected_distribution_type,
            folder_path="configuration_distribution"
        )
        mock_distribution_class.assert_called_once_with(expected_constructor_arg)
        assert result == mock_distribution_instance

class TestAsynchronousDistribution:

    @pytest.fixture(autouse=True)
    def setup(self, get_distribution_experiment):
        # Configuration for the class instance, sourced from EnergyExperiment_Adistr.json
        experiment_description, _ = get_distribution_experiment("A")
        self.config = experiment_description["DistributionMode"]
        self.experiment_id = 123
        self.body = {
            "worker_capacity": 1,
            "number_of_workers": 3,
            "evaluation_time": 1.45
            }

    @patch('configuration_distribution.asynchronous_distribution.publish')
    def test_handle_configuration_distribution_calls_publish(self, mock_publish):
        """
        Tests that handle_configuration_distribution calls the publish function
        with the correct exchange, routing key (experiment_id), and body.
        """

        # ? Setup the mock logger on the mocked base class instance
        mock_logger = MagicMock()

        # * Instantiate the class under test
        distributionAlgorithm = AsynchronousDistribution(self.config)
        distributionAlgorithm.logger = mock_logger
        distributionAlgorithm.handle_configuration_distribution(self.experiment_id, self.body)

        # * Assertions

        # * Assert that the logger was called
        mock_logger.info.assert_called_once_with(
            "Worker dispatched asynchronously"
        )

        # * Assert that the publish function was called with the correct arguments
        mock_publish.assert_called_once_with(
            exchange='get_new_configuration_exchange',
            routing_key=self.experiment_id,
            body=self.body
        )

    def test_dispatch_calls_handle_configuration_distribution(self):
        """
        Tests that dispatch simply calls handle_configuration_distribution.
        """

        # * only need to mock the logger here for a clean test
        with patch('configuration_distribution.distribution_abs') as MockAbstractDistribution:

            # ? Setup mock logger
            mock_instance = MockAbstractDistribution.return_value
            mock_instance.logger = MagicMock()

            distributor = AsynchronousDistribution(self.config)

            # * Replace the method we want to confirm is called with a mock
            distributor.handle_configuration_distribution = MagicMock()
            distributor.dispatch(self.experiment_id, self.body)

            # * Assert that the internal method was called with the correct arguments
            distributor.handle_configuration_distribution.assert_called_once_with(
                self.experiment_id, self.body
            )

    def test_first_it_does_nothing(self):
        """
        Tests that first_it is a pass
        """
        # ? Instantiate the class
        with patch('configuration_distribution.distribution_abs'):
            distributor = AsynchronousDistribution(self.config)

            distributor.first_it(self.experiment_id)

class TestBatchedDistribution:

    @pytest.fixture(autouse=True)
    def setup(self, get_distribution_experiment):
        # Configuration for the class instance, sourced from EnergyExperiment_Bdistr.json
        experiment_description, _ = get_distribution_experiment("B")
        self.config = experiment_description["DistributionMode"]
        self.experiment_id = 123
        self.body = {
            "worker_capacity": 1,
            "number_of_workers": 3,
            "evaluation_time": 1.45
        }

    @patch('logging.getLogger')
    def test_init_success(self, mock_get_logger):
        """Tests successful initialization with a batchSize."""

        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        distributionAlgorithm = BatchedDistribution(self.config)

        # * Assert the call on the specific method of the mock
        mock_logger_instance.info.assert_called_once()
        mock_logger_instance.info.assert_called_with(
            "Batched Distribution initialized with batch size: 5"
        )

        # * Assert internal state
        assert distributionAlgorithm._batch_size == 5
        assert distributionAlgorithm._first_it is True
        assert distributionAlgorithm._barrier is None

    @patch('logging.getLogger')
    def test_init_key_error(self, mock_get_logger):
        """Tests that initialization raises ValueError if 'batchSize' is missing."""

        bad_config = {}

        # * Set up the mock logger instance
        mock_logger_instance = mock_get_logger.return_value

        # * Assert that the function call RAISES the expected exception
        with pytest.raises(ValueError, match="Batched Distribution requires 'batchSize' in description."):
            BatchedDistribution(bad_config)

        # * Assert the side effects (logging) AFTER the exception has been raised.
        mock_logger_instance.error.assert_called_once()
        mock_logger_instance.error.assert_called_with(
            "Description missing 'batchSize'!"
        )

    @patch('configuration_distribution.batched_distribution.publish')
    def test_first_it_initial_call(self, mock_publish):
        """Tests that the first call to first_it publishes the initial batch and flips the flag."""

        # * Setup
        mock_logger = MagicMock()
        distributionAlgorithm = BatchedDistribution(self.config)
        distributionAlgorithm.logger = mock_logger

        # * Call
        result = distributionAlgorithm.first_it(self.experiment_id)

        # * Assertions
        assert result is True
        assert distributionAlgorithm._first_it is False

        # * Assert logger call
        mock_logger.info.assert_called_once_with("Proposing the first 5 configurations")

        # * Assert publish call
        expected_body = json.dumps({"worker_capacity": 5})

        mock_publish.assert_called_once_with(
            exchange='get_new_configuration_exchange',
            routing_key=self.experiment_id,
            body=expected_body
        )

    def test_first_it_subsequent_call(self):
        """Tests that subsequent calls to first_it return False and do nothing."""

        # * Setup
        mock_logger = MagicMock()
        distributionAlgorithm = BatchedDistribution(self.config)
        distributionAlgorithm.logger = mock_logger

        # ? Manually set the flag
        distributionAlgorithm._first_it = False

        # * Call
        result = distributionAlgorithm.first_it(self.experiment_id)

        # * Assertions
        assert result is False
        assert distributionAlgorithm._first_it is False

        # * Assert no logging or publishing occurred
        mock_logger.info.assert_not_called()

    # ? --- Test dispatch and handle_configuration_distribution Flow ---
    @patch('threading.Thread')
    @patch('threading.Barrier')
    def test_dispatch_calls_first_it_and_returns_on_true(self, MockBarrier, MockThread):
        """
        Tests that dispatch respects the first_it result and exits if True.
        """

        # * Setup
        mock_logger = MagicMock()
        distributionAlgorithm = BatchedDistribution(self.config)
        distributionAlgorithm.logger = mock_logger

        # * Mock first_it to immediately return True and check if it was called
        distributionAlgorithm.first_it = MagicMock(return_value=True)

        # * Call
        distributionAlgorithm.dispatch(self.experiment_id, self.body)

        # * Assertions
        distributionAlgorithm.first_it.assert_called_once_with(self.experiment_id)
        MockThread.assert_not_called()
        MockBarrier.assert_not_called()

    @patch('threading.Thread')
    @patch('threading.Barrier')
    @patch('configuration_distribution.batched_distribution.publish')
    def test_dispatch_and_handle_flow(self, mock_publish, MockBarrier, MockThread):
        """
        Tests the entire dispatch flow when first_it returns False.
        This includes barrier creation and thread starting.
        """

        # * Setup
        mock_logger = MagicMock()
        distributionAlgorithm = BatchedDistribution(self.config)
        distributionAlgorithm.logger = mock_logger
        distributionAlgorithm.first_it = MagicMock(return_value=False)

        # * Ensure the barrier is None for the initial creation check
        distributionAlgorithm._barrier = None

        # * Prepare the mock thread instance
        mock_thread_instance = MockThread.return_value

        # * Call dispatch
        distributionAlgorithm.dispatch(self.experiment_id, self.body)

        # * Assertions for dispatch logic
        distributionAlgorithm.logger.info.assert_called_with(
            f"Creating new barrier with size {distributionAlgorithm._batch_size}"
        )

        MockBarrier.assert_called_once_with(distributionAlgorithm._batch_size)

        assert distributionAlgorithm._barrier == MockBarrier.return_value

        MockThread.assert_called_once_with(
            target=distributionAlgorithm.handle_configuration_distribution,
            args=(self.experiment_id, self.body),
            daemon=True
        )

        mock_thread_instance.start.assert_called_once()

        # ? --- Simulate the Thread Call for handle_configuration_distribution ---
        # * Get the mocked barrier instance that was created
        mock_barrier_instance = MockBarrier.return_value

        # * Mock its state and wait() method
        mock_barrier_instance.n_waiting = 2 # ? Simulate 2 workers already waiting
        mock_barrier_instance.wait.return_value = None # ? Ensure wait() doesn't block

        # * Manually call the target method (as the mocked thread would)
        distributionAlgorithm.handle_configuration_distribution(self.experiment_id, self.body)

        # ? --- Assertions for handle_configuration_distribution logic ---

        expected_log_calls = [
            call(f"Creating new barrier with size {distributionAlgorithm._batch_size}"), # ? From dispatch
            call("Waiting for all workers to be synchronized"),
            call('Workers currently waiting 3'), # ? 2 waiting + 1 current = 3
            call("Worker synchronized"),
        ]
        distributionAlgorithm.logger.info.assert_has_calls(expected_log_calls, any_order=False)

        # * Check that the barrier was correctly waited upon
        mock_barrier_instance.wait.assert_called_once()

        # * Check that publish was called
        mock_publish.assert_called_once_with(
            exchange='get_new_configuration_exchange',
            routing_key=self.experiment_id,
            body=self.body
        )

class TestHybridDistribution:

    @pytest.fixture(autouse=True)
    def setup(self, get_distribution_experiment):
        """Set up required configuration and data for tests, sourced from EnergyExperiment_Hdistr.json."""

        experiment_description, _ = get_distribution_experiment("H")
        self.config = experiment_description["DistributionMode"]
        self.experiment_id = 456
        self.body_dict = {
            "worker_capacity": 1,
            "number_of_workers": 3,
            "evaluation_time": 2000  # Time taken for the worker to process config, in milliseconds
        }
        self.body = json.dumps(self.body_dict)

    def test_init_success(self):
        """Tests successful initialization with a batchSize."""

        distributionAlgorithm = HybridDistribution(self.config)

        # * Assert internal state
        assert distributionAlgorithm._batch_size == 5
        assert distributionAlgorithm._first_it is True
        assert distributionAlgorithm._gate is None
        assert distributionAlgorithm._initial_timeout == 5
        assert distributionAlgorithm._number_of_workers == 0
        assert list(distributionAlgorithm._evaluation_times) == []

    @patch('logging.getLogger')
    def test_init_key_error(self, mock_get_logger):
        """Tests that initialization raises ValueError if 'batchSize' is missing."""

        bad_config = {}
        mock_logger_instance = mock_get_logger.return_value

        # * Assert that the function call RAISES the expected exception
        with pytest.raises(ValueError, match="Hybrid Distribution requires 'batchSize' in description."):
            HybridDistribution(bad_config)

        # * Assert the side effects (logging) AFTER the exception
        mock_logger_instance.error.assert_called_once()
        mock_logger_instance.error.assert_called_with(
            "Description missing 'batchSize'!"
        )

    @patch('configuration_distribution.hybrid_distribution.publish')
    def test_first_it_initial_call(self, mock_publish):
        """Tests that the first call to first_it publishes the initial batch and flips the flag."""

        # * Setup
        mock_logger = MagicMock()
        distributionAlgorithm = HybridDistribution(self.config)
        distributionAlgorithm.logger = mock_logger

        # * Call
        result = distributionAlgorithm.first_it(self.experiment_id)

        # * Assertions
        assert result is True
        assert distributionAlgorithm._first_it is False

        # * Assert logger call
        mock_logger.info.assert_called_once_with("Proposing the first 5 configurations")

        # * Assert publish call
        expected_body = json.dumps({"worker_capacity": 5})

        mock_publish.assert_called_once_with(
            exchange='get_new_configuration_exchange',
            routing_key=self.experiment_id,
            body=expected_body
        )

    def test_first_it_subsequent_call(self):
        """Tests that subsequent calls to first_it return False and do nothing."""

        # * Setup
        distributionAlgorithm = HybridDistribution(self.config)
        # ? Manually set the flag
        distributionAlgorithm._first_it = False

        # * Call
        result = distributionAlgorithm.first_it(self.experiment_id)

        # * Assertions
        assert result is False

        # * Assert no state change or publishing occurred
        assert distributionAlgorithm._first_it is False

    @patch('threading.Thread')
    @patch('configuration_distribution.hybrid_distribution.EventGate')
    @patch('configuration_distribution.hybrid_distribution.publish')
    def test_dispatch_and_handle_flow_with_new_gate(self, mock_publish, MockEventGate, MockThread):
        """
        Tests the entire dispatch flow when first_it returns False, including
        gate creation and thread starting. Also checks internal state updates.
        """

        # * Setup
        distributionAlgorithm = HybridDistribution(self.config)
        distributionAlgorithm.logger = MagicMock()
        distributionAlgorithm.first_it = MagicMock(return_value=False)

        # ? Manually set internal state from previous runs for accurate timeout calc
        # ? This simulates enough data for a full proposal (5 configurations)
        # ? Proposal size is 5, Number of workers is 3 (from self.body_dict)
        distributionAlgorithm._evaluation_times = deque(
            [3.0, 3.0, 3.0, 3.0, 3.0], maxlen=distributionAlgorithm._batch_size
        )
        distributionAlgorithm._number_of_workers = self.body_dict["number_of_workers"]

        # * Prepare the mock thread instance
        mock_thread_instance = MockThread.return_value

        # * Prepare the mock gate instance
        mock_gate_instance = MockEventGate.return_value

        # * Call dispatch
        # ? This will update evaluation_times with the new body's time (2000ms)
        distributionAlgorithm.dispatch(self.experiment_id, self.body)

        # ? --- Assertions for dispatch logic ---

        # * Check first_it was called
        distributionAlgorithm.first_it.assert_called_once_with(self.experiment_id)

        # * Check internal state update from body
        # ? The new time (2.0s) should be appended, evicting the oldest sample.
        assert list(distributionAlgorithm._evaluation_times) == [3.0, 3.0, 3.0, 3.0, 2.0]
        assert distributionAlgorithm._number_of_workers == 3

        MockThread.assert_called_once_with(
            target=distributionAlgorithm.handle_configuration_distribution,
            args=(self.experiment_id, self.body),
            daemon=True
        )
        mock_thread_instance.start.assert_called_once()

        # ? --- Simulate the Thread Call for handle_configuration_distribution ---
        distributionAlgorithm.handle_configuration_distribution(self.experiment_id, self.body)

        # ? --- Assertions for Gate creation and use within handle_configuration_distribution ---

        expected_timeout = 9.0

        # * Check EventGate creation
        MockEventGate.assert_called_once()

        MockEventGate.assert_called_with(
            distributionAlgorithm._batch_size,
            expected_timeout,
            distributionAlgorithm._cleanup_gate
        )

        # * Check that the worker waited at the gate
        mock_gate_instance.wait_at_gate.assert_called_once()

        # * Check that the new configuration was published after unblocking from the gate
        mock_publish.assert_called_once_with(
            exchange='get_new_configuration_exchange',
            routing_key=self.experiment_id,
            body=self.body
        )

    @patch('threading.Thread')
    @patch('configuration_distribution.hybrid_distribution.EventGate')
    @patch('configuration_distribution.hybrid_distribution.publish')
    def test_handle_configuration_distribution_reuses_gate(self, mock_publish, MockEventGate, MockThread):
        """
        Tests that handle_configuration_distribution reuses the existing gate
        if one has already been created by a preceding worker.
        """

        # * Setup
        distributionAlgorithm = HybridDistribution(self.config)
        mock_gate_instance = MagicMock()
        distributionAlgorithm._gate = mock_gate_instance

        # * Call the method for a subsequent worker
        distributionAlgorithm.handle_configuration_distribution(self.experiment_id, self.body)

        # * Assertions

        # * MockEventGate's constructor should NOT have been called, as it was reused.
        MockEventGate.assert_not_called()

        # * The worker still waits at the gate.
        mock_gate_instance.wait_at_gate.assert_called_once()

        # * A new configuration is published after the wait.
        mock_publish.assert_called_once_with(
            exchange='get_new_configuration_exchange',
            routing_key=self.experiment_id,
            body=self.body
        )

    def test_cleanup_gate(self):
        """
        Tests the cleanup callback function by ensuring it sets _gate to None.
        """
        # * Setup
        distributionAlgorithm = HybridDistribution(self.config)
        mock_gate = MagicMock()
        distributionAlgorithm._gate = mock_gate

        # * Define dummy stats
        dummy_stats = {"result": "completion"}

        # * Call
        distributionAlgorithm._cleanup_gate(dummy_stats)

        # * Assertions
        assert distributionAlgorithm._gate is None

    def test_zero_arrival_timeout_resets_gate_for_next_wave(self):
        """
        Tests that firing timeout before the arrival of the first worker, 
        resets the gate for the rest of the experiment.
        """
        # * Setup
        distributionAlgorithm = HybridDistribution(self.config)
        gate = distributionAlgorithm._get_or_create_gate()

        # Simulate the timer firing with zero registered arrivals.
        gate.timer.cancel()
        gate._trigger_by_timeout()

        # * Assertions: the stale gate must have been cleaned up already.
        assert distributionAlgorithm._gate is None

        new_gate = distributionAlgorithm._get_or_create_gate()
        assert new_gate is not gate

    def test_dispatch_converts_evaluation_time_from_milliseconds_to_seconds(self):
        """
        Workers report evaluation_time in milliseconds; dispatch must convert it
        to seconds before it feeds the (seconds-based) adaptive timeout logic.
        """
        distributionAlgorithm = HybridDistribution(self.config)
        distributionAlgorithm.first_it = MagicMock(return_value=True)

        body = json.dumps({"worker_capacity": 1, "number_of_workers": 3, "evaluation_time": 4500})
        distributionAlgorithm.dispatch(self.experiment_id, body)

        assert list(distributionAlgorithm._evaluation_times) == [4.5]

    def test_dispatch_discards_none_evaluation_time(self):
        """
        A None evaluation_time (e.g. a Configuration whose results have not yet
        been aggregated) must not be appended, and must not raise.
        """
        distributionAlgorithm = HybridDistribution(self.config)
        distributionAlgorithm.first_it = MagicMock(return_value=True)

        body = json.dumps({"worker_capacity": 1, "number_of_workers": 3, "evaluation_time": None})
        distributionAlgorithm.dispatch(self.experiment_id, body)

        assert list(distributionAlgorithm._evaluation_times) == []

    def test_dispatch_discards_nan_evaluation_time(self):
        """
        A NaN evaluation_time (e.g. every task for a Configuration was marked
        Bad/Outlier/Out-of-bounds) must not be appended, and must not raise or
        poison the adaptive timeout with NaN.
        """
        distributionAlgorithm = HybridDistribution(self.config)
        distributionAlgorithm.first_it = MagicMock(return_value=True)

        body = json.dumps({"worker_capacity": 1, "number_of_workers": 3, "evaluation_time": float("nan")})
        distributionAlgorithm.dispatch(self.experiment_id, body)

        assert list(distributionAlgorithm._evaluation_times) == []

    def test_calculate_next_timeout_stays_in_seconds(self):
        """
        Regression guard for the ms/s unit bug: once enough (already-converted,
        second-denominated) samples are present, the adaptive timeout must stay
        on the order of the observed evaluation times.
        """
        distributionAlgorithm = HybridDistribution(self.config)
        distributionAlgorithm._number_of_workers = 5
        distributionAlgorithm._evaluation_times = deque(
            [2.0] * distributionAlgorithm._batch_size, maxlen=distributionAlgorithm._batch_size
        )

        timeout = distributionAlgorithm._calculate_next_timeout()

        assert timeout == pytest.approx(3.0)  # 2.0s * (1 + TIMEOUT_BUFFER_FACTOR)

    def test_evaluation_times_bounded_by_batch_size(self):
        """
        Test that only the most recent batch_size
        evaluation times are retained, with the oldest evicted first.
        """
        distributionAlgorithm = HybridDistribution(self.config)
        distributionAlgorithm.first_it = MagicMock(return_value=True)

        # Dispatch far more samples than batch_size (5).
        for i in range(20):
            body = json.dumps({"worker_capacity": 1, "number_of_workers": 3, "evaluation_time": i * 1000})
            distributionAlgorithm.dispatch(self.experiment_id, body)

        assert len(distributionAlgorithm._evaluation_times) == distributionAlgorithm._batch_size
        # ? Only the last 5 (converted) samples survive: 15.0, 16.0, 17.0, 18.0, 19.0
        assert list(distributionAlgorithm._evaluation_times) == [15.0, 16.0, 17.0, 18.0, 19.0]


class TestEventGate:
    """Unit tests for the timeout-based synchronization gate (EventGate)."""

    def test_release_on_completion(self):
        """When batchSize workers arrive, the gate releases them all at once."""
        cleanup = MagicMock()
        gate = EventGate(2, 30, cleanup)

        threads = [threading.Thread(target=gate.wait_at_gate) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        for thread in threads:
            assert not thread.is_alive(), "worker stayed blocked at the gate"
        assert gate.triggered

        cleanup.assert_called_once()
        stats = cleanup.call_args[0][0]
        assert stats["result"] == "completion"

    def test_release_on_timeout(self):
        """An incomplete wave is released by the timeout instead of hanging."""
        done = threading.Event()
        captured = {}

        def cleanup(stats):
            captured["stats"] = stats
            done.set()

        # batchSize 5 will never fill with a single worker -> timeout releases it.
        gate = EventGate(5, 0.2, cleanup)
        worker = threading.Thread(target=gate.wait_at_gate)
        worker.start()
        worker.join(timeout=5)

        assert not worker.is_alive()
        assert done.wait(timeout=5), "cleanup was never invoked"
        assert gate.triggered
        assert captured["stats"]["result"] == "timeout"

    def test_late_worker_after_trigger_does_not_double_clean(self):
        """
        Edge case 'worker arrives during the timeout-release window': a worker
        that reaches the gate after it was already triggered must pass through
        without hanging and without firing a second cleanup for the finished wave.
        """
        cleanup = MagicMock()
        gate = EventGate(5, 0.2, cleanup)

        # First worker joins the wave and is released by the timeout.
        first = threading.Thread(target=gate.wait_at_gate)
        first.start()
        first.join(timeout=5)

        assert gate.triggered
        assert cleanup.call_count == 1

        # A worker arriving after the trigger passes the already-open gate and
        # must not produce a second cleanup nor block.
        late = threading.Thread(target=gate.wait_at_gate)
        late.start()
        late.join(timeout=5)

        assert not late.is_alive(), "late worker blocked on a released gate"
        assert cleanup.call_count == 1

    def test_zero_arrival_timeout_triggers_cleanup_immediately(self):
        """
        Tests that firing timeout before the arrival of the first worker,
        immediatly calls the cleanup.
        """
        cleanup = MagicMock()
        gate = EventGate(5, 30, cleanup)

        # Simulate the timer firing with zero registered arrivals.
        gate.timer.cancel()
        gate._trigger_by_timeout()

        assert gate.triggered
        cleanup.assert_called_once()
        stats = cleanup.call_args[0][0]
        assert stats["result"] == "timeout"

    def test_late_worker_after_zero_arrival_timeout_reports_cleanup(self):
        """
        Tests that the late worker must still pass as in the asynchronous mode, 
        while cleanup was called.
        """
        cleanup = MagicMock()
        gate = EventGate(5, 30, cleanup)

        gate.timer.cancel()
        gate._trigger_by_timeout()

        late = threading.Thread(target=gate.wait_at_gate)
        late.start()
        late.join(timeout=5)

        assert not late.is_alive(), "late worker blocked on a released gate"
        assert cleanup.call_count == 1
