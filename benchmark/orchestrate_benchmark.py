import argparse
import logging
import os
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_NODE_PATH = str(PROJECT_ROOT / 'main_node')
if MAIN_NODE_PATH not in sys.path:
    sys.path.insert(0, MAIN_NODE_PATH)

from logger.default_logger import BRISELogConfigurator
from util.shared_tools import chown_files_in_dir, cleanup_benchmark_results
from util.config_detector import ConfigDetector
from analyzer.config import BenchmarkConfig

logging_config_path = os.path.join(MAIN_NODE_PATH, 'logger', 'logging_config.yaml')
if not os.path.exists(logging_config_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logging_config_path = os.path.join(script_dir, 'logger', 'logging_config.yaml')
BRISELogConfigurator(logging_config_path)

host_event_service = "event-service"
port_event_service = 49153
results_storage = "./results/serialized/"


def run_benchmark():
    try:
        from runner.benchmark_runner import BRISEBenchmarkRunner
        runner = BRISEBenchmarkRunner(host_event_service, port_event_service, results_storage)
        try:
            runner.fill_db()
        except Exception as exception:
            logging.error("Benchmarking interrupted: %s" % exception, exc_info=True)
        finally:
            runner.main_api_client.stop_main()
            runner.main_api_client.stop_client()
            chown_files_in_dir(results_storage)
            logging.info("Ownership of dump files changed, exiting.")
    except Exception as exception:
        logging.error("Unable to create BRISEBenchmarkRunner: %s" % exception, exc_info=True)


def analyze(
    results_storage: str = results_storage,
    output_html: str = "./results/reports/benchmark_report.html",
    output_csv: str = "./results/reports/benchmark_all_objectives.csv",
    config_path: str = None,
    interactive_baselines: bool = True
):
    try:
        if config_path is None:
            config_path = ConfigDetector.detect_config_file(base_dir=Path(__file__).resolve().parent)
            if not config_path:
                logging.error("No configuration file found. Please provide a benchmark configuration.")
                return

        logging.info(f"Using configuration: {config_path}")
        config_dict = ConfigDetector.load_config(config_path)
        if not config_dict:
            logging.error("Failed to load configuration file")
            return

        config = BenchmarkConfig.from_json(config_dict)

        # Respect config output directory when user didn't override output paths.
        default_html = "./results/reports/benchmark_report.html"
        default_csv = "./results/reports/benchmark_all_objectives.csv"
        if output_html == default_html and config.output_directory:
            output_html = str(Path(config.output_directory) / "benchmark_report.html")
        if output_csv == default_csv and config.output_directory:
            output_csv = str(Path(config.output_directory) / "benchmark_all_objectives.csv")

        has_comparative_analysis = ConfigDetector.has_comparative_analysis(config_dict)
        if has_comparative_analysis:
            logging.info("Comparative metrics detected - comparative analysis will be performed")

        logging.info(f"Running analyzer on dumps in {results_storage}")

        if interactive_baselines and has_comparative_analysis:
            logging.info("Interactive baseline selection mode enabled")
            from analyzer.orchestration.interactive_baseline_analyzer import InteractiveBaselineAnalyzer
            analyzer = InteractiveBaselineAnalyzer(config)
            analyzer.analyze_with_baseline_selection(output_html, output_csv)
        else:
            from analyzer.orchestration import BenchmarkAnalyzer
            analyzer = BenchmarkAnalyzer(config)
            analyzer.analyze(output_html, output_csv)

        # Keep the default report path in sync with the latest analysis so that
        # init.sh show_report always opens the freshly generated report, not a
        # stale one from a previous run. Always overwrite, don't skip if present.
        # Compare resolved paths so we don't copy a file onto itself when the
        # configured output already points at the default location.
        for generated_str, fallback_str, label in (
            (output_html, default_html, "report"),
            (output_csv, default_csv, "CSV"),
        ):
            generated = Path(generated_str)
            fallback = Path(fallback_str)
            if not generated.exists():
                continue
            if generated.resolve() == fallback.resolve():
                continue
            fallback.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(generated, fallback)
            logging.info("Updated %s at default location: %s", label, fallback)

        logging.info(f"Analyzer completed: {output_html}, {output_csv}")
    except FileNotFoundError as fnf_err:
        logging.warning("Analyzer skipped: %s" % fnf_err)
    except Exception as exception:
        logging.error("Analyzer failed: %s" % exception, exc_info=True)


def orchestrate(skip_analyzer: bool = False, cleanup_before_run: bool = False):
    if cleanup_before_run:
        logging.info("Cleaning up generated files...")
        cleanup_benchmark_results(results_storage.rstrip('/serialized/'))
        logging.info("Cleanup completed.")

    run_benchmark()

    if skip_analyzer:
        logging.info("Skipping analyzer as requested.")
    else:
        analyze(results_storage)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BRISE Benchmark orchestrator")
    parser.add_argument("--mode", choices=["analyse", "benchmark", "cleanup"], default="benchmark")
    parser.add_argument("--skip-analyzer", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--no-interactive", action="store_true")
    args = parser.parse_args()

    if args.mode == "analyse":
        analyze(results_storage, interactive_baselines=not args.no_interactive)
    elif args.mode == "cleanup":
        cleanup_benchmark_results(results_storage.rstrip('/serialized/'))
    else:
        orchestrate(args.skip_analyzer, args.cleanup)
