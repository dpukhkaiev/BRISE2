# BRISE Configuration Distribution Extension

A modular extension for the **BRISE SOFTWARE PRODUCT LINE** that manages how experiment configurations are
dispatched to workers. The introduction of synchronization modi may be suitable for certain configuration runs,
depending on the specific workload.

---

## System Architecture

The extension follows the strategy pattern.

* **`AbstractDistribution`** ([distribution_abs.py](distribution_abs.py)): the base interface ensuring all
  strategies implement the required lifecycle methods. Wraps around the **get_new_configuration_exchange** event.
* **`ConfigurationDistributionOrchestrator`** ([configuration_distribution_orchestrator.py](configuration_distribution_orchestrator.py)):
  uses reflective class loading to instantiate the strategy defined in the experiment's product configuration at
  runtime.
* **`WSClient`** ([../WorkerServiceClient/WSClient_events.py](../WorkerServiceClient/WSClient_events.py)): plugs
  into the framework's main loop before new configuration selection to manage the synchronization.

A batch is counted in completed measurements rather than in worker processes: the framework asks the distribution
for a successor once per measured configuration.

---

## Detailed Class & Function Breakdown

### 1. Asynchronous Distribution ([asynchronous_distribution.py](asynchronous_distribution.py))
The strategy without synchronization. Configurations are sent via the RabbitMQ exchange immediately to the workers
upon generation.

* **`dispatch(...)`**: the entrypoint for the distribution logic. Calls the inner logic directly.
* **`handle_configuration_distribution(...)`**: publishes the `get_new_configuration_exchange` event.
* **`first_it(...)`**: no operation (not required for asynchronous starts).

### 2. Batched Distribution ([batched_distribution.py](batched_distribution.py))
Synchronizes workers using a python barrier to ensure they process tasks in batches of a specific size.

* **`__init__(config)`**: extracts `BatchSize` from the product configuration.
* **`first_it(...)`**: triggers the first set of configurations. It is called by `dispatch` on the very first
  message and requests `BatchSize` configurations.
* **`dispatch(...)`**: creates the barrier when needed and spawns a **daemon thread** to run the logic. This is
  critical to prevent the main event-thread from blocking while waiting for the barrier.
* **`handle_configuration_distribution(...)`**: waits at the barrier. The code execution pauses here until the
  `BatchSize` arrival, at which point all configurations are published simultaneously.

### 3. Hybrid Distribution ([hybrid_distribution.py](hybrid_distribution.py))
A smart barrier approach that prevents the pipeline from stalling due to slow workers or deadlocks by using a
timeoutable gate.

#### The `EventGate` Helper Class
A gate is created per wave and opens either when the batch is complete or when the wave's time limit expires,
whichever comes first, releasing every thread waiting at it. It also measures how long the wave took and how long
its threads waited, and hands those statistics over when the finished wave is cleaned up.

#### The Distribution Class
* **`__init__(config)`**: extracts `BatchSize` and `InitialTimeoutInSeconds` from the product configuration; both are
  mandatory.
* **`first_it(...)`**: as in the batched strategy.
* **`dispatch(...)`**: spawns a **daemon thread** to run the logic, and records the evaluation times reported by
  the workers.
* **`handle_configuration_distribution(...)`**: workers wait at the gate. This allows the logic to release threads
  **either** when a full batch is ready **or** when the maximum waiting time expires.
* **Adaptive timeout**: `InitialTimeoutInSeconds` applies to the first waves only. Once enough evaluation times have been
  observed, every wave is given a timeout derived from how long the preceding configurations actually took, plus a
  safety margin. Workers report evaluation time in milliseconds; it is converted to seconds before being used as a
  timeout.

---

## Configuration

`DistributionMode` is a **mandatory** feature of the
[feature model](../Resources/tests/waffle_models/base.wfl): exactly one strategy has to be selected, and its
parameters belong inside the selected strategy.

| Strategy | Key | `Type` | Parameter 1 | Parameter 2 |
| :--- | :--- | :--- | :--- | :--- |
| **Asynchronous** | `AsynchronousDistribution` | `asynchronous_distribution` | N/A | N/A |
| **Batched** | `BatchedDistribution` | `batched_distribution` | `BatchSize` (Int) | N/A |
| **Hybrid** | `HybridDistribution` | `hybrid_distribution` | `BatchSize` (Int) | `InitialTimeoutInSeconds` (Float) |

### Example Config:
```json
"DistributionMode": {
    "HybridDistribution": {
        "BatchSize": 5,
        "InitialTimeoutInSeconds": 5.0,
        "Type": "hybrid_distribution"
    }
}
```

One product configuration per strategy is shipped in
[../Resources/tests/test_cases_product_configurations](../Resources/tests/test_cases_product_configurations) as
`EnergyExperiment_Adistr.json`, `EnergyExperiment_Bdistr.json` and `EnergyExperiment_Hdistr.json`.
