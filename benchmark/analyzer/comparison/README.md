# Comparative Analysis Module

## Overview

The comparative analysis module enables systematic evaluation of optimization algorithms by:
- **Interactive Baseline Selection**: Choose any executed experiment as a baseline
- **Standardized Metrics**: Normalized improvement, regret, speedup, performance profiles
- **Multi-Baseline Comparison**: Compare against multiple reference algorithms simultaneously
- **Visualization**: Comparative plots, distribution analysis, and performance rankings

---

## Metrics

**Metric Details**:

#### Regret Calculation

**Simple Regret** (per iteration):
```python
regret = abs(best_value - known_optimum)
```

**Time-Based Regret**:
```python
cumulative_regret = sum(abs(value - known_optimum) for value in trajectory)
```

**Time-Based Regret**:
Returns list of `(timestamp, regret)` tuples for time-series analysis.

#### Relative Improvement

**Objective Value**:
```python
NI = (baseline_initial - experiment_best) / (baseline_initial - baseline_final)
```

**Time-to-Target**:
```python
NI = experiment_time / baseline_time
# < 1.0 means faster than baseline
```

**Iteration-to-Target**:
```python
NI = experiment_iters / baseline_iters
# < 1.0 means fewer iterations than baseline
```

#### Performance Profiles

**Performance Ratio**:
```python
r_p,s = t_p,s / min_s(t_p,s)
```
Where `t_p,s` is the metric value for solver `s` on problem `p`.

**Profile**:
```python
ρ_s(τ) = (1/n_p) * |{p : r_p,s ≤ τ}|
```
Fraction of problems where solver `s` is within factor `τ` of best.

---

## Interactive Baseline Selection

### Overview

The interactive baseline selection feature allows users to dynamically choose which executed experiments serve as comparison baselines.

### Benefits

**Flexibility**: Any experiment can be a baseline
**Iterative Workflow**: Compare new versions against previous runs
**Multi-Baseline**: Compare against multiple references simultaneously
**No Re-execution**: Change baselines without rerunning experiments
**Domain-Specific**: Use production systems or reference implementations as baselines

### Selection Workflow

1. **Execute experiments**: Run all test cases normally via `./init.sh up benchmark`
2. **Automatic UI launch**: Browser opens at `http://localhost:8765` showing experiment list
3. **Review experiments**: See metadata (objectives, iterations, final values) for each
4. **Select baselines**: Check one or more experiments to use as baselines
5. **Confirm selection**: Click "Continue with selected baselines"
6. **Analysis proceeds**: All metrics computed using selected baselines
7. **View results**: Report displays comparisons in tables and plots

### Selection Persistence

User selections are saved to `results/baseline_selection.json`:
```json
{
  "benchmark_id": "exp_test_gpr_sobol_quantitybased_timebased",
  "selected_baselines": ["test_case_2", "test_case_9"],
  "timestamp": "2026-02-15T10:30:00"
}
```

**Reuse**: Subsequent analyses automatically load the saved selection
**Override**: Delete the file or use `./init.sh cleanup_report` to force new selection
**Version Control**: Track baseline choices alongside configurations

### Use Cases

**Algorithm Evolution**:
```
Run: algorithm_v1.0
Run: algorithm_v2.0
Select: algorithm_v1.0 as baseline
Result: Measure improvement of v2.0 over v1.0
```

**Multi-Algorithm Comparison**:
```
Run: random_search, genetic_algorithm, bayesian_optimization
Select: random_search and genetic_algorithm as baselines
Result: Compare bayesian_optimization against both
```

**Domain-Specific Baselines**:
```
Run: production_config, baseline_heuristic, new_ml_approach
Select: production_config as baseline
Result: Evaluate new approach against current production performance
```

---

## Comparative Metrics

### Relative Improvement

**Definition**: Relative improvement over baseline

**Variants**:

1. **Objective Value Improvement**
   - Measures quality improvement
   - Range: (-∞, +∞)
   - \> 0: Better than baseline
   - = 0: Same as baseline
   - < 0: Worse than baseline

2. **Time-to-Target Speedup**
   - Measures time efficiency
   - Range: (0, +∞)
   - < 1: Faster than baseline
   - = 1: Same speed as baseline
   - \> 1: Slower than baseline

3. **Iteration-to-Target Speedup**
   - Measures iteration efficiency
   - Range: (0, +∞)
   - < 1: Fewer iterations than baseline
   - = 1: Same iterations as baseline
   - \> 1: More iterations than baseline

**Configuration**:
```json
"RelativeImprovement": {
  "improvementType": ["objective_value", "time_to_target", "iteration_to_target"]
}
```

### Regret Analysis

**Definition**: Distance from known optimal value

**Variants**:

1. **Iteration-Based Regret**
   - X-axis: Iteration number
   - Y-axis: |best_so_far - optimum|
   - Use Case: Convergence speed analysis

2. **Time-Based Regret**
   - X-axis: Wall-clock time (seconds)
   - Y-axis: |best_so_far - optimum|
   - Use Case: Real-world performance

**Requirements**:
- Known global optimum
- Monotonic best-so-far trajectory

**Configuration**:
```json
"RegretAnalysis": {
  "knownOptimum": 0.0,
  "optimumPerObjective": {
    "Y1": 0.0,
    "Y2": 5.0
  },
  "regretType": ["iteration", "time"]
}
```

### Performance Profiles

**Definition**: Cumulative distribution of performance ratios

**Purpose**: Rank algorithms across multiple problems

**Interpretation**:
- Higher curve = better overall performance
- Steep rise at τ=1 = often best solver
- Plateau at τ >> 1 = robust solver

**Requirements**:
- Multiple test cases (≥ 2)
- Same objectives across all test cases
- Complete data for all algorithms

**Configuration**:
```json
"PerformanceProfile": {
  "tauMax": 10.0,
  "tauSteps": 100,
  "objectivesToProfile": ["Y1", "Y2", "Y3"]
}
```

**Reading Performance Profiles**:
```
ρ(τ) = 1.0 at τ = 2.0
→ Algorithm solves 100% of problems within 2× of best performance
```
---
## Configuration Guide

### Full Comparative Configuration

```json
{
  "ComparativeAnalysis": {
    "ComparativeTable": {
      "experiment": true,
      "baseline": true,
      "relativeImprovement": true,
      "convergedAtIteration": true,
      "experimentBest": true,
      "baselineBest": true,
      "finalRegret": true
    },
    "RegretAnalysis": {
      "knownOptimum": 0.0,
      "optimumPerObjective": {
        "Y1": 0.0
      },
      "regretType": [
        "iteration",
        "time"
      ]
    },
    "RelativeImprovement": {
      "improvementType": [
        "objective_value",
        "time_to_target",
        "iteration_to_target"
      ]
    },
    "PerformanceProfile": {
      "tauMax": 5.0,
      "tauSteps": 50,
      "objectivesToProfile": [
        "Y1",
        "Y2",
        "Y3",
        "Y4",
        "Y5"
      ]
    }
  }
}
```

---

## Output

### Comparative Tables

**Format**: CSV and HTML tables

**Columns**:
- Experiment name
- Baseline type
- Relative improvement (objective, time, iterations)
- Converged at iteration
- Experiment best value
- Baseline best value
- Final regret

**Example**:
```
Experiment    Baseline      RI (Obj)  RI (Time)  RI (Iter)  Converged  Exp Best  Base Best
test_case_0   random-search 1.40      0.03       -0.17      27         0.36      0.26
test_case_0   grid-search   1.65      -0.01      -3.38      27         0.36      0.16
```

### Comparative Plots

#### Relative Improvement Plots

**Type**: Grouped bar charts

**Features**:
- One bar per (experiment, baseline) pair
- Color-coded by performance (green=better, yellow/red=worse)
- Reference line at y=1 (baseline performance)
- Separate plots for objective, time, iteration improvements

#### Regret Plots

**Type**: Line charts

**Features**:
- One line per test case
- X-axis: Iterations or time
- Y-axis: Regret (distance to optimum)
- Decreasing curves indicate convergence
- Separate plots for iteration-based and time-based

#### Performance Profile

**Type**: Cumulative distribution

**Features**:
- X-axis: Performance ratio τ
- Y-axis: ρ(τ) - fraction of problems solved within τ× of best
- One curve per algorithm
- Higher curves = better overall performance

---

## Further Reading

- **[Main README](../README.md)**: Overall benchmark documentation