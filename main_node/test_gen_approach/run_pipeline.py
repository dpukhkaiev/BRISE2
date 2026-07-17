"""
Pipeline executing Phase 1 (Parsing + Pairwise generation + Waffle validation)
and Phase 2 (Integration tests) for BRISE SPL.

Assumes BRISE and Waffle are already running.

Usage examples:
    # Full pipeline: generate pairwise configs, validate all, then run tests
    python3 run_pipeline.py

    # Validate only specific pairwise config indices
    python3 run_pipeline.py --configs 3 8 15

    # Skip Phase 1, only run Phase 2 integration tests
    python3 run_pipeline.py --phase2-only

    # Skip Phase 2, only run Phase 1 validation
    python3 run_pipeline.py --phase1-only

    # Run Phase 2 on specific config files only
    python3 run_pipeline.py --phase2-only --test-configs config_3_2-float-5-mo.json config_8_all-types-so.json

    # Run a specific Phase 2 test module
    python3 run_pipeline.py --phase2-only --test-module test_config_selection_loop

"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

MAIN_NODE = Path(__file__).resolve().parent.parent
PHASE1_DIR = MAIN_NODE / "test_gen_approach" / "test_generation"
PHASE2_DIR = MAIN_NODE / "test_gen_approach" / "integration_tests"
OUTPUT_DIR = PHASE1_DIR / "output_configs"
PHASE2_TESTS_DIR = PHASE2_DIR / "integration_modules"

GRAMMAR = str(PHASE1_DIR / "grammar.tx")
WFL = str(PHASE1_DIR / "base.wfl")
MODELS = str(PHASE1_DIR / "WaffleTestingModels")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the BRISE SPL testing pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Phase selection
    phase_group = parser.add_mutually_exclusive_group()
    phase_group.add_argument(
        "--phase1-only", action="store_true",
        help="Run only Phase 1 (pairwise generation + Waffle validation), skip Phase 2",
    )
    phase_group.add_argument(
        "--phase2-only", action="store_true",
        help="Run only Phase 2 (integration tests), skip Phase 1",
    )

    # Phase 1 options
    p1 = parser.add_argument_group("Phase 1 options")
    p1.add_argument(
        "--configs", type=int, nargs="+", metavar="INDEX",
        help="Pairwise config indices to validate (e.g. --configs 3 8 15) "
             "Default: all 85 configs",
    )
    # Phase 2 options
    p2 = parser.add_argument_group("Phase 2 options")
    p2.add_argument(
        "--test-configs", nargs="+", metavar="FILENAME",
        help="Run Phase 2 tests only on these config filenames "
             "(e.g. --test-configs config_3_2-float-5-mo.json) "
             "Default: all configs in output_configs/",
    )
    p2.add_argument(
        "--test-module", type=str, metavar="MODULE",
        help="Run only a specific Phase 2 test module "
             "(e.g. --test-module test_config_selection_loop)",
    )
    p2.add_argument(
        "--pytest-args", type=str, default="",
        help="Additional arguments to pass to pytest (e.g. '--pytest-args \"-q\"')",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose output",
    )

    return parser.parse_args()



def run_phase1(config_indices=None, verbose=False):

    print("PHASE 1 — Pairwise generation + Waffle validation")


    if str(PHASE1_DIR) not in sys.path:
        sys.path.insert(0, str(PHASE1_DIR))

    from pairwise_generator import generate_pairwise
    from selenium_validator import WaffleSeleniumValidator

    print("\nGenerating pairwise configurations...")
    all_configs = generate_pairwise(GRAMMAR, WFL)
    print(f"  Generated {len(all_configs)} pairwise configurations")

    # Filter to specified indices
    if config_indices is not None:
        index_set = set(config_indices)
        configs = [c for c in all_configs if c.index in index_set]
        missing = index_set - {c.index for c in configs}
        if missing:
            print(f"  Warning: indices {sorted(missing)} not found in pairwise output")
        print(f"  Selected {len(configs)} configs: {sorted(c.index for c in configs)}")
    else:
        configs = all_configs

    if not configs:
        print("  No configurations to validate. Skipping Phase 1")
        return []

    # Step 3 Selenium validation
    validator = WaffleSeleniumValidator(
        grammar_path=GRAMMAR,
        wfl_path=WFL,
        models_dir=MODELS,
    )
    valid_configs = validator.validate_all(configs)

    # Summary
    print(f"\n{'─' * 40}")
    print(f"Phase 1 complete.")
    print(f"  Valid   : {len(valid_configs)}/{len(configs)}")
    print(f"  Invalid : {len(configs) - len(valid_configs)}/{len(configs)}")
    print(f"  Output  : {OUTPUT_DIR}/")
    if valid_configs:
        for vc in valid_configs:
            print(f"    - config_{vc.index}_{vc.context_variant}.json")
    print()

    return valid_configs



def run_phase2(test_configs=None, test_module=None, pytest_args="", verbose=False):
    """Run Phase 2: pytest integration tests against Phase 1 output configs.

    Uses subprocess to invoke pytest from main_node/ so that all BRISE imports
    resolve correctly.
    """
    print("PHASE 2 — Integration tests")

    available = sorted(f.name for f in OUTPUT_DIR.glob("*.json"))
    if not available:
        print("\n  No config files found in output_configs/. Nothing to test.")
        print("  Run Phase 1 first or check the output directory.")
        return 1

    # configs to test
    if test_configs is not None:
        missing = [c for c in test_configs if c not in available]
        if missing:
            print(f"\n  Warning: config files not found: {missing}")
        selected = [c for c in test_configs if c in available]
        if not selected:
            print("  No matching config files. Aborting Phase 2.")
            return 1
        print(f"\n  Testing {len(selected)} config(s): {selected}")
    else:
        selected = available
        print(f"\n  Testing all {len(selected)} configs in output_configs/")

    cmd = [sys.executable, "-m", "pytest"]

    # Test target
    if test_module:
        module_path = PHASE2_TESTS_DIR / f"{test_module}.py"
        if not module_path.exists():
            # Try with test_ prefix
            module_path = PHASE2_TESTS_DIR / f"test_{test_module}.py"
        if not module_path.exists():
            print(f"\n  Test module not found: {test_module}")
            print(f"  Available modules:")
            for f in sorted(PHASE2_TESTS_DIR.glob("test_*.py")):
                print(f"    - {f.stem}")
            return 1
        cmd.append(str(module_path.relative_to(MAIN_NODE)))
    else:
        cmd.append(str(PHASE2_TESTS_DIR.relative_to(MAIN_NODE)))

    # Filter to specific config files using pytest -k
    if test_configs is not None:
        # Build a pytest -k expression that matches only the requested configs
        k_expr = " or ".join(c.replace(".json", "").replace(".", "_") for c in selected)
        cmd.extend(["-k", k_expr])

    cmd.append("-v")
    cmd.append("--tb=short")

    # Additional user args
    if pytest_args:
        cmd.extend(pytest_args.split())

    print(f"\n  Command: {' '.join(cmd)}")
    print(f"  Working dir: {MAIN_NODE}\n")
    print("─" * 40)

    result = subprocess.run(cmd, cwd=str(MAIN_NODE))

    print(f"\n{'─' * 40}")
    print(f"Phase 2 complete. pytest exit code: {result.returncode}")
    return result.returncode



def main():
    args = parse_args()

    start_time = time.time()
    phase2_exit = 0

    # Phase 1
    if not args.phase2_only:
        run_phase1(
            config_indices=args.configs,
            verbose=args.verbose,
        )

    # Phase 2
    if not args.phase1_only:
        phase2_exit = run_phase2(
            test_configs=args.test_configs,
            test_module=args.test_module,
            pytest_args=args.pytest_args,
            verbose=args.verbose,
        )

    elapsed = time.time() - start_time
    minutes, seconds = divmod(int(elapsed), 60)

    print()
    print(f"Pipeline finished in {minutes}m {seconds}s.")

    sys.exit(phase2_exit)


if __name__ == "__main__":
    main()
