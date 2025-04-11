import argparse
import logging

from benchmark_runner import BRISEBenchmarkRunner
from logger.default_logger import BRISELogConfigurator
from shared_tools import chown_files_in_dir

BRISELogConfigurator()  # Configuring logging


def run_benchmark():
    # Container creation performs --volume on `./results/` folder. Change wisely results_storage.
    host_event_service = "event-service"
    port_event_service = 49153
    results_storage = "./results/serialized/"
    try:
        runner = BRISEBenchmarkRunner(host_event_service, port_event_service, results_storage)
        try:
            # ---    Add User defined benchmark scenarios execution below  ---#
            # --- Possible variants: benchmark_test, fill_db ---#
            runner.fill_db()

            # --- Helper method to move outdated experiments from `./results` folder ---#
            runner.move_redundant_experiments(location=runner.results_storage + "repeater_outdated/")

            # ---   Add User defined benchmark scenarios execution above   ---#
        except Exception as exception:
            logging.error("The Benchmarking process interrupted by an exception: %s" % exception, exc_info=True)
        finally:
            runner.main_api_client.stop_main()
            runner.main_api_client.stop_client()
            chown_files_in_dir(results_storage)
            logging.info("The ownership of dump files was changed, exiting.")
    except Exception as exception:
        logging.error("Unable to create BRISEBenchmarkRunner instance: %s" % exception, exc_info=True)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The entry point of BRISE Benchmark service.")
    parser.add_argument("--mode", choices=["analyse", "benchmark"],
                        help="Mode in which Benchmarking functionality should be run.")
    args = parser.parse_args()

    run_benchmark()
