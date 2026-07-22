# BRISE Configuration Distribution Extension

A modular extension for the **BRISE SOFTWARE PRODUCTLINE** that manages how experiment configurations are dispatched to workers. The introduction of synchronization modi may be suitible for certain configuration runs, depending on the specific workload.

---

## System Architecture

The extension follows a provider pattern managed by an **Orchestrator**. It works as a **Factory** pattern.

* **`AbstractDistribution`**: The base interface ensuring all strategies implement the required lifecycle methods. Wrapps around the **get_new_configuration_exchange** Event.
* **`ConfigurationDistributionOrchestrator`**: Uses reflective class loading to instantiate the strategy defined in the experiment's JSON configuration at runtime.
* **`WSClient`**: Plugs into the framework's main loop before new configuration selection to manage the synchronization.



---

## Detailed Class & Function Breakdown

### 1. Asynchronous Distribution (`AsynchronousDistribution.py`)
The default strategy. Configurations are sent via the RabbitMQ exchange immediately to the workers upon generation.

* **`dispatch(...)`**: The entrypoint for the distribution logic.
Handles the overall state of the synchronization objects.
Calls the inner logic.
* **`handle_configuration_distribution(experiment_id, body)`**: Directly calls the `publish` utility to send the `get_new_configuration_exchange` event.
* **`first_it(...)`**: No-op (not required for asynchronous starts).

### 2. Batched Distribution (`BatchedDistribution.py`)
Synchronizes workers using a python barrier to ensure they process tasks in batches of a specific size.

* **`__init__(config)`**: Extracts `batchSize` from the payload and initializes a `threading.Barrier`.
* **`first_it(experiment_id)`**: Triggers the first set of configurations.
It publishes a special message to RabbitMQ with `worker_capacity` set to the batch size, ensuring the framework generates enough initial configurations to fill the first batch.
* **`dispatch(experiment_id, body)`**: Spawns a **daemon thread** to run the logic. This is critical to prevent the main event-thread from blocking while waiting for the barrier.
* **`handle_configuration_distribution(...)`**: Calls `self._barrier.wait()`. The code execution pauses here until the $N$-th worker (where $N$ is `batchSize`) arrives, at which point all configurations are published simultaneously.

### 3. Hybrid Distribution (`HybridDistribution.py`)
A smart barrier approach that prevents the pipeline from stalling due to slow workers or deadlocks by using a timeoutable gate.

#### The `EventGate` Helper Class
* **`__init__(...)`**: Initializes a `threading.Event` and a `threading.Timer`.
* **`_trigger_by_timeout()`**: A callback that opens the gate regardless of the arrival count if the specified time limit is reached.
* **`wait_at_gate()`**: Increments the `arrival_count`. If the count equals `batch_size`, it cancels the timer and opens the gate manually.

#### The Distribution Class
* **`_get_or_create_gate()`**: Ensures thread-safe management of the gate. If a gate is currently open or non-existent, it initializes a new one for the next wave.
* **`handle_configuration_distribution(...)`**: Workers call `gate.wait_at_gate()`. This allows the logic to release threads **either** when a full batch is ready **or** a maximum waiting time exspires.
* **`_cleanup_gate(stats)`**: Resets the gate reference in the orchestrator so the next arriving workers get a fresh gate.

---

## Configuration

To use a specific strategy, add the `DistributionMode` object to your experiment's JSON description. However, when no mode description is provided the orchestrator defaults to asynchronous behavior:

| Strategy | Key | Parameter 1 | Parameter 2 |
| :--- | :--- | :--- | :--- |
| **Asynchronous** | `AsynchronousDistribution` | N/A | N/A |
| **Batched** | `BatchedDistribution` | `batchSize` (Int) | N/A |
| **Hybrid** | `HybridDistribution` | `batchSize` (Int) | `timeout` (Float) |

### Example Config:
```json
"DistributionMode": {
        "HybridDistribution": {
                "Type": "HybridDistribution"
        },
        "batchSize": {
                "Int": "5"
        },
        "timeout": {
                "Int": "5"
        }
    }