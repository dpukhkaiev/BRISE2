# Minimum Working Example (Comparative Benchmark)

This guide is the shortest path to run the benchmark analyzer with comparative metrics and baseline selection.

## 1) Where to start

Run all commands from the `/benchmark` directory:

### Analyse existing serialized experiments (fastest path)

Use the experiment dumps already available in `./results/serialized/` and run:

```bash
./init.sh analyse
```

### Run a fresh benchmark from CLI (executes `fill_db()` on default)

If you want to generate new dumps first:

```bash
./init.sh up benchmark
```

This runs `BRISEBenchmarkRunner.fill_db()` and then runs analysis (unless `--skip-analyzer` is used).


## 2) What the analysis workflow does

The analysis pipeline in `orchestrate_benchmark.py` does the following:

1. Detects configuration (`ConfigDetector`) and loads `Benchmark` settings.
2. Loads serialized experiment dumps from `./results/serialized/`.
3. If comparative metrics are active, opens baseline selection (interactive UI) and stores selection in `./results/baseline_selection.json`.
4. Builds objective-wise plots and tables.
5. Computes comparative metrics (regret, normalized improvement, optional performance profile).
6. Exports HTML and CSV outputs into `./results/reports/`.

## 3) Feature model and template to use

Use this template for the MWE:

- `benchmark/configs/benchmark_templates/comparative_benchmark_template.json`

The feature model behind these options is:

- `benchmark/configs/benchmark_feature_model/benchmark_feature_model.wfl`

For plot normalization under `ObjectiveAxis.NormalizationStrategy`, the model supports:

- `MinOverAll` (`min_over_all_experiments`)
- `MaxOverAll` (`max_over_all_experiments`)

`normalize: true` applies the selected strategy to all compared trajectories in a plot.

## 4) Baseline selection explanation

Baseline selection chooses one or more executed experiments as reference algorithms.

- Each remaining experiment is compared against matched baseline(s).
- Comparative outputs include normalized improvement, regret curves, and comparative tables.

If a baseline selection already exists, it is reused automatically on the next `analyse` run.

## 5) Test cases analyzed in `fill_db()`

`fill_db()` covers representative scenario classes from `main_node/Resources/tests/test_cases_product_configurations/`:

- `test_case_0.json`: flat search space with numeric (float) parameters.
- `test_case_4.json`: mixed float/nominal search space.
- `test_case_9.json`: mixed float/nominal with random DCH setup.
- `test_case_2.json`: all parameter types with random DCH.
- `test_case_2_wo_dch.json`: all parameter types without DCH.
- `test_grid_search_baseline.json`: grid-search baseline run.
- `test_random_search_baseline.json`: random-search baseline run.

Together these provide a small but diverse set for comparing optimization behavior and baseline quality.

