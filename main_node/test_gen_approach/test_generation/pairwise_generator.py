"""
Pairwise Configuration Generator

Generates a minimal set of configurations that covers all pairs of feature
values (pairwise / 2-wise coverage) using the allpairspy library

Workflow:
    1. Parse feature dimensions from the WFL file (wfl_parser_textx.py)
    2. Add the Context variant as an extra pairwise dimension
    3. Run AllPairs
    4. Output a list of PairwiseConfig objects ready for Waffle API validation

Context variants encode the test SearchSpace + Objective combinations:
    - SearchSpace: 2-float or float-nom or all-types
    - Objectives : so (single objective) or 2-mo or 5-mo

Usage:
    from pairwise_generator import generate_pairwise, CONTEXT_VARIANTS

    configs = generate_pairwise("grammar.tx", "base_0_3_0.wfl")
    print(f"{len(configs)} pairwise configurations generated")
    for cfg in configs[:3]:
        print(cfg)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

from allpairspy import AllPairs

from wfl_parser_textx import WflParserTextX


# Context variants

CONTEXT_VARIANTS: List[str] = [
    "2-float-so",
    "2-float-2-mo",
    "2-float-5-mo",
    "float-nom-so",
    "float-nom-2-mo",
    "float-nom-5-mo",
    "all-types-so",
    "all-types-2-mo",
    "all-types-5-mo",
]


# Data class for a single pairwise configuration
@dataclass
class PairwiseConfig:
    index: int
    context_variant: str
    # One selected path per feature dimension
    selections: List[str] = field(default_factory=list)

    def is_selected(self, path: str) -> bool:
        """Return True if *path* is selected and does NOT end in '.None'."""
        return path in self.selections and not path.endswith(".None")

    def get_selected(self, prefix: str) -> str | None:
        """
        Return the first selection that starts with *prefix* and is not .None
        Useful for locating which child of a XOR group was chosen
        """
        for s in self.selections:
            if s.startswith(prefix) and not s.endswith(".None"):
                return s
        return None

    def __repr__(self) -> str:
        active = [s for s in self.selections if not s.endswith(".None")]
        return (
            f"PairwiseConfig(index={self.index}, "
            f"context={self.context_variant!r}, "
            f"active_features={len(active)}/{len(self.selections)})"
        )


# Main generator
def generate_pairwise(
    grammar_path: str,
    wfl_path: str,
    context_variants: List[str] = CONTEXT_VARIANTS,
) -> List[PairwiseConfig]:
    # Step 1 parse feature model
    parser = WflParserTextX(grammar_path, wfl_path)
    feature_dims: List[List[str]] = parser.parse_features()

    # Step 2 append context variant dimension
    all_dims = feature_dims + [context_variants]

    # Step 3 run AllPairs
    configs: List[PairwiseConfig] = []
    for i, row in enumerate(AllPairs(all_dims)):
        # row is a plain list: one selected value per dimension
        *feature_selections, ctx = row
        configs.append(PairwiseConfig(
            index=i,
            context_variant=ctx,
            selections=feature_selections,
        ))

    return configs



# Summary helpers

def print_summary(configs: List[PairwiseConfig], feature_dims: List[List[str]]) -> None:
    # Print a compact overview of the generated configurations
    print(f"\nTotal pairwise configurations : {len(configs)}")
    print(f"Feature dimensions (parser)   : {len(feature_dims)}")
    print(f"Total dimensions (+ context)  : {len(feature_dims) + 1}")

    # Count how often each context variant appears
    ctx_counts: Dict[str, int] = {}
    for cfg in configs:
        ctx_counts[cfg.context_variant] = ctx_counts.get(cfg.context_variant, 0) + 1
    print("\nContext variant distribution:")
    for variant, count in sorted(ctx_counts.items()):
        print(f"  {variant:<20} {count:>3} configs")

    # Count active (no .None) feature selections
    active_counts = [len([s for s in cfg.selections if not s.endswith(".None")])
                     for cfg in configs]
    avg_active = sum(active_counts) / len(active_counts) if active_counts else 0
    print(f"\nAvg active features per config: {avg_active:.1f} / {len(feature_dims)}")



# CLI entry point
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python pairwise_generator.py <grammar.tx> <file.wfl>")
        print("Example: python pairwise_generator.py grammar.tx base_0_3_0.wfl")
        sys.exit(1)

    grammar_path = sys.argv[1]
    wfl_path = sys.argv[2]

    parser = WflParserTextX(grammar_path, wfl_path)
    feature_dims = parser.parse_features()

    configs = generate_pairwise(grammar_path, wfl_path)

    print_summary(configs, feature_dims)

    print("\nFirst 5 configurations:")
    print("=" * 70)
    for cfg in configs[:5]:
        print(f"\n[{cfg.index}] context={cfg.context_variant}")
        for sel in cfg.selections:
            marker = "  ✓" if not sel.endswith(".None") else "  -"
            print(f"  {marker} {sel}")
