import unittest
import logging
import json
import threading
from unittest.mock import patch, MagicMock, call

from configuration_distribution.configurationDistributionOrchestrator import ConfigurationDistributionOrchestrator
from configuration_distribution.batchedDistribution import BatchedDistribution
from configuration_distribution.hybridDistribution import HybridDistribution, EventGate
from configuration_distribution.asynchronousDistribution import AsynchronousDistribution

# disable logging
logging.disable(logging.CRITICAL)

class TestConfigurationDistributionOrchestrator(unittest.TestCase):

    def setUp(self):
        """Set up a new orchestrator instance for each test."""
        self.orchestrator = ConfigurationDistributionOrchestrator()

    # Test 1: Using EnergyExperiment_Adistr.json config
    @patch('configuration_distribution.configurationDistributionOrchestrator.reflective_class_import')
    def test_get_distribution_asynchronous(self, mock_reflective_import):
        """
        Tests the AsynchronousDistribution config from EnergyExperiment_Adistr.json
        """
        # --- Arrange ---
        mock_distribution_instance = MagicMock(spec=AsynchronousDistribution)
        mock_distribution_class = MagicMock(return_value=mock_distribution_instance)
        mock_reflective_import.return_value = mock_distribution_class

        # This is the expected class name to be imported
        expected_distribution_type = "AsynchronousDistribution"
        
        # This is the config from your Adistr.json file
        distribution_config = {
            "DistributionMode": {
                "AsynchronousDistribution": {
                        "Type": "AsynchronousDistribution"
                }
            }
        }
        
        # This is the inner dictionary passed to the class constructor
        expected_constructor_arg = distribution_config["DistributionMode"]

        # --- Act ---
        result = self.orchestrator.get_distribution(distribution_config)

        # --- Assert ---
        mock_reflective_import.assert_called_once_with(
            class_name=expected_distribution_type,
            folder_path="configuration_distribution"
        )
        mock_distribution_class.assert_called_once_with(expected_constructor_arg)
        self.assertEqual(result, mock_distribution_instance)

    # Test 2: Using EnergyExperiment_Bdistr.json config
    @patch('configuration_distribution.configurationDistributionOrchestrator.reflective_class_import')
    def test_get_distribution_batched(self, mock_reflective_import):
        """
        Tests the BatchedDistribution config from EnergyExperiment_Bdistr.json
        """
        # --- Arrange ---
        mock_distribution_instance = MagicMock(spec=BatchedDistribution)
        mock_distribution_class = MagicMock(return_value=mock_distribution_instance)
        mock_reflective_import.return_value = mock_distribution_class

        # This is the expected class name to be imported
        expected_distribution_type = "BatchedDistribution"
        
        # This is the config from your Bdistr.json file
        distribution_config = {
            "DistributionMode": {
                "BatchedDistribution": {
                        "Type": "BatchedDistribution"
                },
                "batchSize": {
                        "Int": "5"
                }
            }
        }
        
        # This is the inner dictionary passed to the class constructor
        expected_constructor_arg = distribution_config["DistributionMode"]

        # --- Act ---
        result = self.orchestrator.get_distribution(distribution_config)

        # --- Assert ---
        mock_reflective_import.assert_called_once_with(
            class_name=expected_distribution_type,
            folder_path="configuration_distribution"
        )
        mock_distribution_class.assert_called_once_with(expected_constructor_arg)
        self.assertEqual(result, mock_distribution_instance)

    # Test 3: Using EnergyExperiment_Hdistr.json config
    @patch('configuration_distribution.configurationDistributionOrchestrator.reflective_class_import')
    def test_get_distribution_hybrid(self, mock_reflective_import):
        """
        Tests the HybridDistribution config from EnergyExperiment_Hdistr.json
        """
        # --- Arrange ---
        mock_distribution_instance = MagicMock(spec=HybridDistribution)
        mock_distribution_class = MagicMock(return_value=mock_distribution_instance)
        mock_reflective_import.return_value = mock_distribution_class

        # This is the expected class name to be imported
        expected_distribution_type = "HybridDistribution"
        
        # This is the config from your Hdistr.json file
        distribution_config = {
            "DistributionMode": {
                "HybridDistribution": {
                        "Type": "HybridDistribution"
                },
                "batchSize": {
                        "Int": "5"
                }
            }
        }
        
        # This is the inner dictionary passed to the class constructor
        expected_constructor_arg = distribution_config["DistributionMode"]

        # --- Act ---
        result = self.orchestrator.get_distribution(distribution_config)

        # --- Assert ---
        mock_reflective_import.assert_called_once_with(
            class_name=expected_distribution_type,
            folder_path="configuration_distribution"
        )
        mock_distribution_class.assert_called_once_with(expected_constructor_arg)
        self.assertEqual(result, mock_distribution_instance)

    @patch('configuration_distribution.configurationDistributionOrchestrator.reflective_class_import')
    def test_get_distribution_failure_defaults_to_asynchronous(self, mock_reflective_import):
        """
        Tests the "failure path" where an invalid configuration is provided,
        triggering the 'except' block and falling back to the default.
        """
        # --- Arrange ---
        # 1. Set up the mocks
        with patch.object(self.orchestrator, 'logger', new_callable=MagicMock) as mock_logger:
            mock_distribution_instance = MagicMock(spec=AsynchronousDistribution)
            mock_distribution_class = MagicMock(return_value=mock_distribution_instance)
            mock_reflective_import.return_value = mock_distribution_class

            # 2. Define an invalid input configuration
            #    This will cause a KeyError in the try block.
            invalid_config = {}

            # 3. Define the expected default configuration that the
            #    orchestrator creates internally.
            expected_default_config = {
                "AsynchronousDistribution": {
                    "Type": "AsynchronousDistribution"
                }
            }

            # --- Act ---
            result = self.orchestrator.get_distribution(invalid_config)

            # --- Assert ---
            # 1. Check that the logger was called with the correct info messages
            self.assertEqual(mock_logger.info.call_count, 2)
            mock_logger.info.assert_any_call("No valid 'distributionMode' key found in Configuration description.")
            mock_logger.info.assert_any_call("Asynchronous Distribution is selected as default.")

            # 2. Check that reflective_class_import was called with the default class name
            mock_reflective_import.assert_called_once_with(
                class_name="AsynchronousDistribution",
                folder_path="configuration_distribution"
            )
            
            # 3. Check that the returned class was instantiated with the default config
            mock_distribution_class.assert_called_once_with(expected_default_config)

            # 4. Check that the final result is the default mock instance
            self.assertEqual(result, mock_distribution_instance)

class TestAsynchronousDistribution(unittest.TestCase):

    def setUp(self):
        # Configuration for the class instance
        self.config = {
            "AsynchronousDistribution": {
                    "Type": "AsynchronousDistribution"
            }
        }
        self.experiment_id = 123
        self.body = {
            "worker_capacity": 1,
            "number_of_workers": 3,
            "repetition_time": 1.45
            }

        pass

    @patch('configuration_distribution.asynchronousDistribution.publish')
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
            
            # * assert, that calling it doesn't raise an error.
            try:
                distributor.first_it(self.experiment_id)
            except Exception as e:
                self.fail(f"first_it unexpectedly raised an exception: {e}")

class TestBatchedDistribution(unittest.TestCase):

    def setUp(self):
        # ? required 'batchSize' in config description
        self.config =   {
            "BatchedDistribution": {
                "Type": "BatchedDistribution"
            },
            "batchSize": {
                "Int": "5"
            }
        }
        self.experiment_id = 123
        self.body = {
            "worker_capacity": 1,
            "number_of_workers": 3,
            "repetition_time": 1.45
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
        self.assertEqual(distributionAlgorithm._batch_size, 5)
        self.assertTrue(distributionAlgorithm._first_it)
        self.assertIsNone(distributionAlgorithm._barrier)

    @patch('logging.getLogger')
    def test_init_key_error(self, mock_get_logger):
        """Tests that initialization raises ValueError if 'batchSize' is missing."""

        bad_config = {}
        
        # * Set up the mock logger instance
        mock_logger_instance = mock_get_logger.return_value
        
        # * Assert that the function call RAISES the expected exception
        with self.assertRaisesRegex(ValueError, "Batched Distribution requires 'batchSize' in description."):
            BatchedDistribution(bad_config)
        
        # * Assert the side effects (logging) AFTER the exception has been caught by the assertRaises context manager.
        mock_logger_instance.error.assert_called_once()
        mock_logger_instance.error.assert_called_with(
            "Description missing 'batchSize'!"
        )

    @patch('configuration_distribution.batchedDistribution.publish')
    def test_first_it_initial_call(self, mock_publish):
        """Tests that the first call to first_it publishes the initial batch and flips the flag."""
        
        # * Setup
        mock_logger = MagicMock()
        distributionAlgorithm = BatchedDistribution(self.config)
        distributionAlgorithm.logger = mock_logger
        
        # * Call
        result = distributionAlgorithm.first_it(self.experiment_id)

        # * Assertions
        self.assertTrue(result)
        self.assertFalse(distributionAlgorithm._first_it)
        
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
        self.assertFalse(result)
        self.assertFalse(distributionAlgorithm._first_it)
        
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
    @patch('configuration_distribution.batchedDistribution.publish')
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
            f"Creating new barrier with size {self.config['batchSize']['Int']}"
        )

        MockBarrier.assert_called_once_with(distributionAlgorithm._batch_size)

        self.assertEqual(distributionAlgorithm._barrier, MockBarrier.return_value)
        
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

    # ? --- Test broken-barrier recovery (incomplete wave) ---
    @patch('configuration_distribution.batchedDistribution.publish')
    def test_handle_recovers_from_broken_barrier(self, mock_publish):
        """
        If a wave is left incomplete (e.g. a worker dies, or worker_capacity is 0
        so the batch never fills and the barrier gets aborted), waiting workers
        must not hang: the broken barrier is discarded and the worker returns.
        """
        distribution_algorithm = BatchedDistribution(self.config)
        distribution_algorithm.logger = MagicMock()

        broken_barrier = threading.Barrier(distribution_algorithm._batch_size)
        broken_barrier.abort()  # simulate the incomplete / dead-worker wave
        distribution_algorithm._barrier = broken_barrier

        distribution_algorithm.handle_configuration_distribution(self.experiment_id, self.body)

        # * The broken barrier is dropped so the next wave starts clean...
        self.assertIsNone(distribution_algorithm._barrier)
        # * ...and this worker does not proceed to publish for the failed wave.
        mock_publish.assert_not_called()
        distribution_algorithm.logger.warning.assert_called_once()

    @patch('threading.Thread')
    def test_dispatch_replaces_broken_barrier(self, MockThread):
        """A subsequent dispatch replaces a broken barrier with a fresh one."""
        distribution_algorithm = BatchedDistribution(self.config)
        distribution_algorithm.logger = MagicMock()
        distribution_algorithm.first_it = MagicMock(return_value=False)

        broken_barrier = threading.Barrier(distribution_algorithm._batch_size)
        broken_barrier.abort()
        distribution_algorithm._barrier = broken_barrier

        distribution_algorithm.dispatch(self.experiment_id, self.body)

        self.assertIsNotNone(distribution_algorithm._barrier)
        self.assertIsNot(distribution_algorithm._barrier, broken_barrier)
        self.assertFalse(distribution_algorithm._barrier.broken)


class TestHybridDistribution(unittest.TestCase):

    def setUp(self):
        """Set up required configuration and data for tests."""
  
        self.config = {
            "HybridDistribution": {
                "Type": "HybridDistribution"
            },
            "batchSize": {
                "Int": "5"
            }
        }
        self.experiment_id = 456
        self.body_dict = {
            "worker_capacity": 1,
            "number_of_workers": 3,
            "repetition_time": 2.0  # Time taken for the worker to process config
        }
        self.body = json.dumps(self.body_dict)

    def test_init_success(self):
        """Tests successful initialization with a batchSize."""
        
        distributionAlgorithm = HybridDistribution(self.config)
        
        # * Assert internal state
        self.assertEqual(distributionAlgorithm._batch_size, 5)
        self.assertTrue(distributionAlgorithm._first_it)
        self.assertIsNone(distributionAlgorithm._gate)
        self.assertEqual(distributionAlgorithm._initial_timeout, 5)
        self.assertEqual(distributionAlgorithm._number_of_workers, 0)
        self.assertEqual(distributionAlgorithm._evaluation_times, [])

    @patch('logging.getLogger')
    def test_init_key_error(self, mock_get_logger):
        """Tests that initialization raises ValueError if 'batchSize' is missing."""

        bad_config = {}
        mock_logger_instance = mock_get_logger.return_value
        
        # * Assert that the function call RAISES the expected exception
        with self.assertRaisesRegex(ValueError, "Hybrid Distribution requires 'batchSize' in description."):
            HybridDistribution(bad_config)
        
        # * Assert the side effects (logging) AFTER the exception
        mock_logger_instance.error.assert_called_once()
        mock_logger_instance.error.assert_called_with(
            "Description missing 'batchSize'!"
        )

    @patch('configuration_distribution.hybridDistribution.publish')
    def test_first_it_initial_call(self, mock_publish):
        """Tests that the first call to first_it publishes the initial batch and flips the flag."""
        
        # * Setup
        mock_logger = MagicMock()
        distributionAlgorithm = HybridDistribution(self.config)
        distributionAlgorithm.logger = mock_logger
        
        # * Call
        result = distributionAlgorithm.first_it(self.experiment_id)

        # * Assertions
        self.assertTrue(result)
        self.assertFalse(distributionAlgorithm._first_it)
        
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
        self.assertFalse(result)
        
        # * Assert no state change or publishing occurred
        self.assertFalse(distributionAlgorithm._first_it)

    @patch('threading.Thread')
    @patch('configuration_distribution.hybridDistribution.EventGate')
    @patch('configuration_distribution.hybridDistribution.publish')
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
        distributionAlgorithm._evaluation_times = [3.0, 3.0, 3.0, 3.0, 3.0]
        distributionAlgorithm._number_of_workers = self.body_dict["number_of_workers"]
        
        # * Prepare the mock thread instance
        mock_thread_instance = MockThread.return_value
        
        # * Prepare the mock gate instance
        mock_gate_instance = MockEventGate.return_value
        
        # * Call dispatch
        # ? This will update evaluation_times with the new body's time (2.0)
        distributionAlgorithm.dispatch(self.experiment_id, self.body) 

        # ? --- Assertions for dispatch logic ---
        
        # * Check first_it was called
        distributionAlgorithm.first_it.assert_called_once_with(self.experiment_id)

        # * Check internal state update from body
        # ? The new time (2.0) should be appended.
        self.assertEqual(distributionAlgorithm._evaluation_times, [3.0, 3.0, 3.0, 3.0, 3.0,2.0])
        self.assertEqual(distributionAlgorithm._number_of_workers, 3)

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
    @patch('configuration_distribution.hybridDistribution.EventGate')
    @patch('configuration_distribution.hybridDistribution.publish')
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
        self.assertIsNone(distributionAlgorithm._gate)


class TestEventGate(unittest.TestCase):
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
            self.assertFalse(thread.is_alive(), "worker stayed blocked at the gate")
        self.assertTrue(gate.triggered)

        cleanup.assert_called_once()
        stats = cleanup.call_args[0][0]
        self.assertEqual(stats["result"], "completion")

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

        self.assertFalse(worker.is_alive())
        self.assertTrue(done.wait(timeout=5), "cleanup was never invoked")
        self.assertTrue(gate.triggered)
        self.assertEqual(captured["stats"]["result"], "timeout")

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

        self.assertTrue(gate.triggered)
        self.assertEqual(cleanup.call_count, 1)

        # A worker arriving after the trigger passes the already-open gate and
        # must not produce a second cleanup nor block.
        late = threading.Thread(target=gate.wait_at_gate)
        late.start()
        late.join(timeout=5)

        self.assertFalse(late.is_alive(), "late worker blocked on a released gate")
        self.assertEqual(cleanup.call_count, 1)


if __name__ == '__main__':
    unittest.main()