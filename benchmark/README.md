# BRISE Benchmark Module

A comprehensive benchmarking and comparative analysis system for optimization algorithms. 
This module enables automated experiment evaluation, statistical analysis, and interactive visualization of optimization performance.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Workflows](#workflows)
- [Plot Types](#plot-types)
- [Comparative Analysis](#comparative-analysis)
- [Advanced Topics](#advanced-topics)
- [Commands](#commands)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- Docker and docker-compose
- BRISE services running (main-node, worker, event-service)
- Python 3.7+ (for local development)

### Run a Complete Benchmark

```bash
# 1. Configure using Waffle (recommended)
./init.sh waffle

# 2. Run benchmark and analysis
./init.sh up benchmark

# 3. View results (auto-opens in browser)
./init.sh show_report

# 4. Clean up when done
./init.sh cleanup
```

### Analysis Only (If execution results already exist)

```bash
# Analyze existing experiment dumps
./init.sh analyse
```

---

## Features

### Core Capabilities

#### **Multi-Objective Optimization Analysis**
- Automatic detection of all numeric objectives (Y1, Y2, Y3, ...)
- Direction-aware analysis (minimize or maximize)
- Per-objective visualization and metrics
- Aggregate performance profiles across objectives

#### **Visualization Suite**
- **Improvement Plots**: Track best-so-far progression over iterations or measured time
- **Box Plots**: Statistical distribution comparison across algorithms
- **Performance Profiles**: Algorithm ranking across multiple problems
- **Regret Analysis**: Distance from known optimum over time/iterations

#### **Comparative Analysis**
- Interactive baseline selection from executed experiments
- Normalized improvement metrics (objective value, time, iterations)
- Performance profiles across multiple test cases
- Regret analysis (iteration-based and time-based)
- Statistical distribution comparison via box plots

#### **Advanced Metrics**
- **Relative Improvement**: 
  - Objective value improvement
  - Time-to-target speedup
  - Iteration-to-target speedup
- **Regret Analysis**:
  - Iteration-based regret
  - Time-based regret
- **Performance Profiles**: Cross-problem algorithm ranking

#### **Interactive Reports**
- Multi-tab HTML reports
- SVG export for all plots
- Sortable, filterable tables
- CSV data export
- Automatic browser preview

---

## Architecture

### Module Structure

```
benchmark/
├── orchestrate_benchmark.py    # Main entry point
├── runner/
│   └── benchmark_runner.py     # Experiment execution engine
│
├── analyzer/                   # Analysis pipeline
│   ├── config/                 # Configuration management
│   │   └── benchmark_config.py
│   │
│   ├── data_pipeline/          # Data processing
│   │   ├── experiment_loader.py
│   │   ├── experiment_parser.py
│   │   ├── metric_extractor.py
│   │   └── data_processor.py
│   │
│   ├── visualization/          # Plot and report generation
│   │   ├── plot_generator.py
│   │   ├── table_generator.py
│   │   └── report_generator.py
│   │
│   ├── orchestration/          # High-level coordination
│   │   ├── benchmark_analyzer.py
│   │   ├── comparative_integration.py
│   │   └── comparative_orchestrator.py
│   │
│   └── comparison/             # Comparative analysis
│       ├── README.md           # Detailed comparison docs
│       ├── baseline_manager.py
│       ├── comparison_processor.py
│       ├── comparative_metrics.py
│       └── ...
│
├── configs/                    # Configuration templates
│   ├── benchmark_templates/
│   │   ├── benchmark_template.json
│   │   ├── comparative_benchmark_template.json
│   │   └── ...
│   └── benchmark_feature_model/
│       └── benchmark_feature_model.wfl
│
└── results/                    # Output directory
    ├── serialized/             # Experiment dumps (.pkl)
    └── reports/                # Generated reports (HTML, CSV, ZIP)
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **orchestrate_benchmark.py** | CLI entry point, workflow coordination |
| **benchmark_runner.py** | Execute experiments via BRISE API |
| **experiment_loader.py** | Load .pkl files from disk |
| **experiment_parser.py** | Validate and structure experiment data |
| **metric_extractor.py** | Auto-discover objectives, extract trajectories |
| **data_processor.py** | Normalize, transform, compute best-so-far |
| **plot_generator.py** | Create all plot types (improvement, box, etc.) |
| **table_generator.py** | Generate summary statistics tables |
| **report_generator.py** | Assemble multi-tab HTML reports |
| **benchmark_analyzer.py** | Orchestrate entire analysis pipeline |
| **comparison/** | Baseline execution and comparative metrics |

---

## Configuration

### Using Waffle (Recommended)

Waffle provides a visual configuration wizard:

```bash
./init.sh waffle
```

Then:
1. Open http://localhost:8001/wizard/initialize/
2. Paste `benchmark_feature_model.wfl` content
3. Click "Configure product manually"
4. Fill in fields and download `configuration.json`
5. Save to `benchmark/configs/benchmark_templates/configuration.json`

### Manual Configuration

See `configs/benchmark_templates/` for examples.

#### Basic Configuration

```json
{
  "Benchmark": {
    "Report": {
      "outputDirectory": "./results/reports/"
    },
    "Experiment": {
      "name": "My Benchmark",
      "description": "Optimization algorithm comparison",
      "objectivesToMeasure": ["Y1", "Y2", "Y3"]
    },
    "Table": {
      "task": true,
      "model": true,
      "iterations": true,
      "finalBestValue": true,
      "runtime": true
    },
    "Plot_0": {
      "PlotType": {
        "ConvergencePlot": { ... }
      }
    }
  }
}
```

### Configuration Fields

#### Experiment Settings
- `name`: Benchmark name
- `description`: Description for reports
- `objectivesToMeasure`: List of objectives to analyze

#### Plot Settings
- `PlotType`: One of `ConvergencePlot`, `CustomPlot`, `BoxPlot`
- `enableGrouping`: Group multiple runs of same test case
- `normalize`: Apply normalization
- `objectivesToPlot`: Which objectives to include

#### Comparative Analysis
- `showSummaryTable`: Show/hide comparative summary table tab in report
- `ComparativeTable.speedupFactor`: Show/hide `RI (Time)` and `RI (Iterations)` columns
- `RegretAnalysis.regretType`: `["iteration"]`, `["time"]`, or both
- `RelativeImprovement.improvementType`: Types of improvement to calculate
- `PerformanceProfile.objectivesToProfile`: Objectives for profile

#### Grouping and Known Optima
- `enableGrouping`: Aggregate repetitions into mean plus/minus std bands
- `CustomGrouping.valueGroups`: Map metadata values to display labels using dot-paths
- `CustomGrouping.autoGroupBy`: Optional fallback label builder from metadata paths
- `KnownOptima`: Per-objective or per-instance optimum map used by regret and optimum reference lines

---

## Workflows

### 1. Standard Benchmark Workflow

```
┌─────────────────┐
│ Configure       │
│ (Waffle/Manual) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Run Experiments │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate .pkl   │
│ dumps           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Analyze Results │
│ (analyzer)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HTML Report     │
│ (auto-opens)    │
└─────────────────┘
```

### 2. Analysis-Only Workflow

```
┌─────────────────┐
│ Existing .pkl   │
│ files           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ./init.sh       │
│ analyse         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HTML Report     │
│ (auto-opens)    │
└─────────────────┘
```

### 3. Comparative Benchmark Workflow

```
┌─────────────────┐
│ Configure with  │
│ Baselines       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Run Experiments │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Comparative     │
│ Analysis        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Select          │
│ Baseline        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Report with     │
│ Comparisons     │
└─────────────────┘
```

---

## Plot Types

### 1. Convergence Plot
**Purpose**: Track optimization progress over iterations

**Features**:
- Best-so-far trajectory
- Multiple algorithms on same plot
- Baseline overlays (random/grid search)
- Automatic Y-axis scaling

**Use Case**: See how quickly algorithms converge

**Example**:
```json
"Plot_0": {
  "PlotType": {
    "ConvergencePlot": {
      "Type": "convergence_plot",
      "enableGrouping": false,
      "MetricAxis": {
        "metricDescription": "iterations completed",
        "label": "Iteration",
        "scale": "linear"
      },
      "ObjectiveAxis": {
        "objectivesToPlot": ["Y1", "Y2"],
        "normalize": true,
        "label": "Objective Value"
      }
    }
  }
}
```

### 2. Box Plot
**Purpose**: Statistical distribution comparison

**Features**:
- Quartiles, median, mean, outliers
- Algorithm-to-algorithm comparison
- Baseline inclusion
- Variance analysis

**Use Case**: Compare algorithm robustness and consistency

**Key Insight**: Narrow boxes = consistent performance

**Example**:
```json
"Plot_1": {
  "PlotType": {
    "BoxPlot": {
      "Type": "box_plot",
      "enableGrouping": false,
      "ObjectiveAxis": {
        "objectivesToPlot": ["Y1"]
      }
    }
  }
}
```

### 3. Custom Plot 
**Purpose**: Custom-specialized plots (e.g. iterations over time, to track how long each iteration of algorithms took to compute)

**Features**:
- Custom axis definitions (e.g. time, iterations)
- Real-world performance view

**Use Case**: When analyzing specific performance metrics like iterations x time

### 4. Performance Profile
**Purpose**: Algorithm ranking across multiple problems

**Features**:
- Cumulative distribution of performance ratios
- Cross-problem comparison
- Statistical significance

**Use Case**: Determine best overall algorithm

**Auto-Generated**: When multiple test cases exist

### 5. Regret Analysis Plots
**Purpose**: Distance from known optimum

**Features**:
- Iteration-based regret
- Time-based regret
- Convergence rate analysis

**Use Case**: Validate algorithm quality when optimum is known

---

## Comparative Analysis

### Overview

Comparative analysis compares measured experiment trajectories against user-selected baseline experiments. The report can include normalized improvement, speedup factors, regret, and performance profiles.

**See [`analyzer/comparison/README.md`](analyzer/comparison/README.md) for detailed metric definitions.**

---

### Central Guide

This section is the single place to understand how comparative analysis works in this benchmark pipeline.

#### 1) Baseline Selection

- Run analysis with comparative metrics enabled.
- If interactive mode is enabled (default), a browser UI opens and you select one or multiple executed experiments as baselines.
- Selections are persisted (`baseline_selection.json`) and reused in later runs until changed/cleared.
- Selected baseline experiments are excluded from the normal experiment list to avoid double counting in plots and tables.

Run benchmark + analysis:

```bash
./init.sh up benchmark
```

Run analysis only on existing dumps:

```bash
./init.sh analyse
```

#### 2) Relative Improvement

- `objective_value`: compares best objective quality against baseline trajectory.
- `time_to_target`: speedup factor based on runtime to target.
- `iteration_to_target`: speedup factor based on iterations to target.

Interpretation:

- `> 1.0` generally indicates better/faster than baseline.
- `< 1.0` indicates worse/slower than baseline.
- `1.0` indicates parity.

#### 3) Performance Profile

- Aggregates comparisons across objectives/problems.
- Shows how often each approach is within a performance ratio threshold (`tau`).
- Useful for robust cross-problem ranking, not just single-objective winners.

Key config:

- `PerformanceProfile.tauMax`
- `PerformanceProfile.tauSteps`
- `PerformanceProfile.objectivesToProfile`

#### 4) Regret and Known Optima

- Regret requires known optimum values.
- You can define optima globally per objective/instance in `KnownOptima`.
- `RegretAnalysis.optimumPerObjective` overrides `KnownOptima` for overlapping keys.
- `RegretAnalysis.knownOptimum` is a fallback single value.

Recommended pattern:

```json
"KnownOptima": {
  "kroA100.tsp": 21282,
  "pr439.tsp": 107217
}
```

#### 5) Grouping (for cleaner, comparable plots)

Grouping aggregates repeated runs into a mean line with a plus/minus std confidence band.

- Enable with `enableGrouping: true` on a plot.
- `CustomGrouping.valueGroups` maps concrete metadata values to display labels.
- `CustomGrouping.autoGroupBy` optionally builds labels from metadata paths when no explicit mapping matches.
- Typical paths: `hhpc_variant`, `mh_type`, `tuning_variant`, `problem_instance`.

Example:

```json
"CustomGrouping": {
  "valueGroups": [
    {
      "path": "ConfigurationSelection.Predictor.Model_0.Surrogate.Instance",
      "groups": [
        { "value": "3.4", "displayName": "BRR-H-TPE" },
        { "value": "2.5", "displayName": "FRAMAB-H-BRR" }
      ]
    }
  ],
  "autoGroupBy": [
    { "path": "hhpc_variant", "useValueOnly": true }
  ]
}
```

#### 6) Comparative Table Controls

`ComparativeAnalysis.showSummaryTable` controls if the comparative table section is rendered in the report.

`ComparativeAnalysis.ComparativeTable` controls columns:

- `relativeImprovement` controls `RI (Objective)`
- `speedupFactor` controls `RI (Time)` and `RI (Iterations)`
- `finalRegret`, `convergedAtIteration`, `experimentBest`, `baselineBest`, `experiment`, `baseline`

#### 7) Minimal Comparative Config Example

```json
{
  "Benchmark": {
    "KnownOptima": {
      "Y1": 0.0
    },
    "ComparativeAnalysis": {
      "showSummaryTable": true,
      "ComparativeTable": {
        "experiment": true,
        "baseline": true,
        "relativeImprovement": true,
        "speedupFactor": true,
        "convergedAtIteration": true,
        "experimentBest": true,
        "baselineBest": true,
        "finalRegret": true
      },
      "RelativeImprovement": {
        "improvementType": ["objective_value", "time_to_target", "iteration_to_target"]
      },
      "RegretAnalysis": {
        "optimumPerObjective": {
          "Y1": 0.0
        },
        "regretType": ["iteration", "time"]
      },
      "PerformanceProfile": {
        "tauMax": 5.0,
        "tauSteps": 50,
        "objectivesToProfile": ["Y1", "Y2", "Y3"]
      }
    }
  }
}
```

#### 8) Data and Outputs

Expected experiment dump structure (`.pkl`):

- `measured_configurations`
- per-configuration `results`/`averaged_result`
- `start_time` and `end_time` for time-based metrics

Generated outputs:

- HTML report: `results/reports/benchmark_report.html`
- Combined CSV: `results/reports/benchmark_all_objectives.csv`
- Per-objective CSV files: `results/reports/benchmark_objective_<objective>.csv`
- ZIP bundle: `results/reports/benchmark_all_tables.zip`

---

## Commands

### Basic Commands

| Command | Description |
|---------|-------------|
| `./init.sh up benchmark` | Execute benchmark and generate report |
| `./init.sh analyse` | Analyze existing experiments (no execution) |
| `./init.sh show_report` | Open latest report in browser |
| `./init.sh cleanup` | Remove all generated files (.pkl, .csv, .html, .zip) |
| `./init.sh cleanup_report` | Remove reports and baseline selection only |
| `./init.sh waffle` | Start Waffle configuration wizard |

## Contributing

When adding new features:

1. Update feature model (`.wfl`)
2. Add config parsing in `benchmark_config.py`
3. Implement feature in appropriate module
4. Add tests and documentation
5. Update README