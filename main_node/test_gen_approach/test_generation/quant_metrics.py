"""
Metric abbreviations
  FC  = Feature Coverage
  TSS = Test Suite Size
  CSR = Configuration Space Reduction
  ICR = Invalid Configuration Ratio
  TO  = Tuple Occurrence / pairwise coverage
  RC  = Redundant Configurations
  CD  = Configuration Diversity (Jaccard)

"""

import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from wfl_parser_textx import WflParserTextX
from pairwise_generator import generate_pairwise


GRAMMAR_PATH = "grammar.tx"
WFL_PATH = "base.wfl"
OUTPUT_DIR = Path("output_configs")


# Cross-tree constraint pairs that cannot coexist in any valid WFL configuration.

INFEASIBLE_PAIRS: set = {
    frozenset({"NSGA2", "MOEAD"}),
    frozenset({"NSGA2", "MOEAD_GEN"}),
    frozenset({"LinearRegression", "Pure"}),
    frozenset({"SupportVectorRegression", "Pure"}),
    frozenset({"GradientBoostingRegressor", "Pure"}),
    frozenset({"BayesianRidgeRegression", "Pure"}),
    frozenset({"MultiArmedBandit", "Pure"}),
    frozenset({"TreeParzenEstimator", "Pure"}),
    frozenset({"TreeParzenEstimator", "DynamicCompositional"}),
    frozenset({"TreeParzenEstimator", "Portfolio"}),
    frozenset({"MultiLayerPerceptronRegressor", "Pure"}),
    frozenset({"BestMultiPointProposal", "Portfolio"}),
}


def _all_keys(obj) -> set:
    # Recursively collect all dict keys from a nested JSON object
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(k)
            keys |= _all_keys(v)
    return keys


def get_parser_features(grammar_path: str, wfl_path: str) -> list:
    # Return all feature value lists from the WFL parser (one list per dimension
    parser = WflParserTextX(grammar_path, wfl_path)
    return parser.parse_features()


def covered_by_pairwise(all_values: set, configs) -> set:
    # Return feature values that appear in at least one pairwise config's selections
    covered = set()
    for cfg in configs:
        for val in all_values:
            last = val.split(".")[-1]
            if any(last == s.split(".")[-1] for s in cfg.selections):
                covered.add(val)
    return covered


def covered_by_output(all_values: set, output_dir: Path) -> set:
    # Return feature values that appear in at least one valid output JSON config
    if not output_dir.exists():
        return set()
    texts = [f.read_text() for f in output_dir.glob("*.json")]
    covered = set()
    for val in all_values:
        last = val.split(".")[-1]
        if any(last in text for text in texts):
            covered.add(val)
    return covered


def configuration_space_reduction(
    feature_dims: list,
    pairwise_count: int,
    context_count: int = 9,
) -> dict:
    """
    Compute Configuration Space Reduction (CSR).

    Theoretical exhaustive space = product of all WFL dimension sizes and context variants.
    This is the number of configurations that would need to be tested without any
    combinatorial reduction strategy

    """
    exhaustive = 1
    for dim in feature_dims:
        exhaustive *= len(dim)
    exhaustive *= context_count

    csr_ratio = pairwise_count / exhaustive
    return {
        "exhaustive_theoretical": exhaustive,
        "pairwise_count": pairwise_count,
        "csr_ratio": csr_ratio,
        "reduction_pct": (1 - csr_ratio) * 100,
    }


def configuration_diversity(output_dir: Path) -> dict:
    """
    Compute Jaccard-based diversity across all pairs of valid output configs

    Returns avg, min, max diversity and number of pairs evaluated
    """
    if not output_dir.exists():
        return {"avg": 0.0, "min": 0.0, "max": 0.0, "pairs": 0}

    json_files = sorted(output_dir.glob("*.json"))
    if len(json_files) < 2:
        return {"avg": 0.0, "min": 0.0, "max": 0.0, "pairs": len(json_files)}

    feature_sets = [_all_keys(json.loads(f.read_text())) for f in json_files]

    distances = []
    for a, b in combinations(feature_sets, 2):
        union = a | b
        d = 1.0 - len(a & b) / len(union) if union else 0.0
        distances.append(d)

    return {
        "avg": sum(distances) / len(distances),
        "min": min(distances),
        "max": max(distances),
        "pairs": len(distances),
    }


def tuple_occurrence(output_dir: Path, feature_dims: list) -> dict:
    """
    Count how often each cross-dimensional feature pair (2-tuple) appears across
    the valid output configs

    A pair is counted as 'covered' if it appears in at least one valid output config.
    Occurrence per pair is measured by checking if both feature names (last path
    segment) appear as JSON keys in a config

    Returns occurrence statistics and both coverage percentages.
    """
    if not output_dir.exists():
        return {}

    json_files = sorted(output_dir.glob("*.json"))
    if not json_files:
        return {}

    config_key_sets = [_all_keys(json.loads(f.read_text())) for f in json_files]

    # Non-.None values per dimension
    non_none_dims = [[v for v in dim if not v.endswith(".None")] for dim in feature_dims]

    # Cross-dimensional pairs, infeasible pairs excluded from the start
    def _infeasible(v_i, v_j) -> bool:
        return frozenset({v_i.split(".")[-1], v_j.split(".")[-1]}) in INFEASIBLE_PAIRS

    all_cross_pairs = [
        (v_i, v_j)
        for i in range(len(non_none_dims))
        for j in range(i + 1, len(non_none_dims))
        for v_i in non_none_dims[i]
        for v_j in non_none_dims[j]
    ]
    infeasible_count = sum(1 for v_i, v_j in all_cross_pairs if _infeasible(v_i, v_j))
    pairs = [p for p in all_cross_pairs if not _infeasible(*p)]

    # Count occurrences: how many valid configs contain both features of a pair
    occurrence = {}
    for v_i, v_j in pairs:
        s_i, s_j = v_i.split(".")[-1], v_j.split(".")[-1]
        occurrence[(v_i, v_j)] = sum(
            1 for ks in config_key_sets if s_i in ks and s_j in ks
        )

    covered = sum(1 for p in pairs if occurrence[p] > 0)
    counts = [occurrence[p] for p in pairs]

    # Redundant Configurations (RC): excess tuple occurrences beyond the first
    rc_total = sum(max(0, c - 1) for c in counts)
    rr = rc_total / len(pairs) if pairs else 0.0
    # Efficiency score: fraction of total tuple work that was non-redundant
    total_tuple_work = sum(counts)
    efficiency = covered / total_tuple_work if total_tuple_work else 1.0

    return {
        "total_pairs": len(pairs),
        "infeasible_pairs": infeasible_count,
        "covered_pairs": covered,
        "coverage_pct": 100 * covered / len(pairs) if pairs else 0,
        "min_occurrence": min(counts) if counts else 0,
        "max_occurrence": max(counts) if counts else 0,
        "avg_occurrence": sum(counts) / len(counts) if counts else 0,
        # RC metrics
        "rc_total": rc_total,
        "redundancy_ratio": rr,
        "efficiency_score": efficiency,
    }


def compute_metrics(
    grammar_path: str = GRAMMAR_PATH,
    wfl_path: str = WFL_PATH,
    output_dir: Path = OUTPUT_DIR,
) -> dict:
    feature_dims = get_parser_features(grammar_path, wfl_path)
    all_values = [v for dim in feature_dims for v in dim]
    all_values_set = set(all_values)
    non_none_set = {v for v in all_values_set if not v.endswith(".None")}
    total = len(all_values_set)
    total_non_none = len(non_none_set)

    configs = generate_pairwise(grammar_path, wfl_path)

    pairwise_covered = covered_by_pairwise(all_values_set, configs)
    pairwise_covered_non_none = pairwise_covered & non_none_set

    output_covered = covered_by_output(all_values_set, output_dir)
    output_covered_non_none = output_covered & non_none_set

    valid_configs = list(output_dir.glob("*.json")) if output_dir.exists() else []

    csr = configuration_space_reduction(feature_dims, len(configs))
    diversity = configuration_diversity(output_dir)
    to = tuple_occurrence(output_dir, feature_dims)

    invalid_count = len(configs) - len(valid_configs)
    icr = invalid_count / len(configs) if configs else 0.0

    return {
        "feature_dimensions": len(feature_dims),
        # Feature Coverage (incl. .None) ---
        "total_feature_values": total,
        "pairwise_configs": len(configs),
        "pairwise_covered": len(pairwise_covered),
        "pairwise_coverage_pct": 100 * len(pairwise_covered) / total if total else 0,
        "valid_configs": len(valid_configs),
        "output_covered": len(output_covered),
        "output_coverage_pct": 100 * len(output_covered) / total if total else 0,
        "uncovered_by_output": sorted(all_values_set - output_covered),
        # Feature Coverage (excl. .None) ---
        "total_feature_values_non_none": total_non_none,
        "pairwise_covered_non_none": len(pairwise_covered_non_none),
        "pairwise_coverage_pct_non_none": 100 * len(pairwise_covered_non_none) / total_non_none if total_non_none else 0,
        "output_covered_non_none": len(output_covered_non_none),
        "output_coverage_pct_non_none": 100 * len(output_covered_non_none) / total_non_none if total_non_none else 0,
        "uncovered_by_output_non_none": sorted(non_none_set - output_covered_non_none),
        # Configuration Space Reduction
        "csr": csr,
        # Invalid Configuration Ratio
        "invalid_configs": invalid_count,
        "icr": icr,
        "vcr": 1.0 - icr,
        # Configuration Diversity (Jaccard)
        "diversity": diversity,
        # Tuple Occurrence + Redundant Configurations
        "tuple_occurrence": to,
    }


def print_report(metrics: dict) -> None:
    print("Phase 1 Pipeline — Quantitative Coverage Metrics")

    print(f"\nWFL Feature Model (wfl_parser_textx.py)")
    print(f"Feature dimensions : {metrics['feature_dimensions']}")
    print(f"Total feature values (incl. .None): {metrics['total_feature_values']}")
    print(f"Total feature values (excl. .None): {metrics['total_feature_values_non_none']}")

    print(f"\nPairwise Generation (pairwise_generator.py)")
    print(f"Configurations     : {metrics['pairwise_configs']}")
    print(f"Values covered (incl. .None): {metrics['pairwise_covered']}/{metrics['total_feature_values']}"
          f" ({metrics['pairwise_coverage_pct']:.1f}%)")
    print(f"Values covered (excl. .None): {metrics['pairwise_covered_non_none']}/{metrics['total_feature_values_non_none']}"
          f" ({metrics['pairwise_coverage_pct_non_none']:.1f}%)")

    csr = metrics.get("csr", {})
    if csr:
        print(f"\nConfiguration Space Reduction (CSR)")
        print(f"Exhaustive (theoretical): {csr['exhaustive_theoretical']:,}")
        print(f"Pairwise generated      : {csr['pairwise_count']}")
        print(f"CSR ratio               : {csr['csr_ratio']:.2e}")
        print(f"Reduction               : {csr['reduction_pct']:.4f}%")

    print(f"\nValid Output Configs (output_configs/)")
    print(f"Valid configs      : {metrics['valid_configs']}"
          f" / {metrics['pairwise_configs']} generated"
          f"  (VCR {metrics['vcr']*100:.1f}%  |  ICR {metrics['icr']*100:.1f}%)")
    print(f"Values covered (incl. .None): {metrics['output_covered']}/{metrics['total_feature_values']}"
          f" ({metrics['output_coverage_pct']:.1f}%)")
    print(f"Values covered (excl. .None): {metrics['output_covered_non_none']}/{metrics['total_feature_values_non_none']}"
          f" ({metrics['output_coverage_pct_non_none']:.1f}%)")

    uncovered = metrics["uncovered_by_output_non_none"]
    if uncovered:
        print(f"Uncovered (excl. .None) ({len(uncovered)}):")
        for v in uncovered:
            print(f"  {v}")

    d = metrics.get("diversity", {})
    if d.get("pairs", 0) > 0:
        print(f"\nConfiguration Diversity (Jaccard, {d['pairs']} config pairs)")
        print(f"Avg diversity      : {d['avg']:.4f}")
        print(f"Min diversity      : {d['min']:.4f}")
        print(f"Max diversity      : {d['max']:.4f}")

    to = metrics.get("tuple_occurrence", {})
    if to:
        print(f"\nTuple Occurrence (2-wise, over {metrics['valid_configs']} valid configs)")
        print(f"Feasible pairs     : {to['total_pairs']} (excl. {to['infeasible_pairs']} infeasible)")
        print(f"Covered pairs      : {to['covered_pairs']}/{to['total_pairs']}"
              f" ({to['coverage_pct']:.1f}%)")
        print(f"Occurrence avg/min/max: {to['avg_occurrence']:.2f} / "
              f"{to['min_occurrence']} / {to['max_occurrence']}")
        print(f"\nRedundant Configurations (RC, over valid pairs)")
        print(f"Excess occurrences (RC): {to['rc_total']}")
        print(f"Redundancy ratio (RR)  : {to['redundancy_ratio']:.4f}"
              f"  ({to['redundancy_ratio']*100:.2f}% avg excess per valid pair)")
        print(f"Efficiency score       : {to['efficiency_score']:.4f}"
              f"  (non-redundant work / total tuple work)")

    print()


if __name__ == "__main__":
    metrics = compute_metrics()
    print_report(metrics)
