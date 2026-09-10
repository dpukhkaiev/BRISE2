from analyzer.config.benchmark_config import (
    CustomGroupingConfig,
    ValueGroupEntry,
    ValueGroupSpec,
)
from analyzer.util.grouping_utils import build_group_label


def test_value_group_maps_matching_value():
    config = CustomGroupingConfig(
        value_groups=[
            ValueGroupSpec(
                path="hhpc_variant",
                groups=[
                    ValueGroupEntry(value="S-TPE", display_name="S-TPE"),
                    ValueGroupEntry(value="BRR-H-TPE", display_name="BRR-H-TPE"),
                ],
            )
        ]
    )

    meta = {"hhpc_variant": "BRR-H-TPE"}
    assert build_group_label(meta, "", None, config) == "BRR-H-TPE"


def test_unmatched_value_falls_back_to_filename():
    config = CustomGroupingConfig(
        value_groups=[
            ValueGroupSpec(
                path="hhpc_variant",
                groups=[ValueGroupEntry(value="S-TPE", display_name="S-TPE")],
            )
        ]
    )

    # experiment whose hhpc_variant is not in the list
    meta = {"hhpc_variant": "FRAMAB-H-BRR"}
    label = build_group_label(meta, "exp_name", "exp_tsp_hh_abc123(0)(1).pkl", config)
    # should fall back to the source filename (stripped of repetition suffix and .pkl)
    assert label == "exp_tsp_hh_abc123"


def test_value_groups_match_list_items():
    config = CustomGroupingConfig(
        value_groups=[
            ValueGroupSpec(
                path="model_types_list",
                groups=[ValueGroupEntry(value="TreeParzenEstimator", display_name="S-TPE")],
            )
        ]
    )

    meta = {"model_types_list": ["ModelMock", "TreeParzenEstimator"]}
    assert build_group_label(meta, "", None, config) == "S-TPE"


def test_no_grouping_config_falls_back_to_filename():
    meta = {"hhpc_variant": "S-BRR"}
    label = build_group_label(meta, "exp_name", "my_exp_3.pkl", None)
    assert label == "my_exp"


def test_nested_path_lookup_via_raw_description():
    """ExperimentMetadata.get() should traverse nested description dicts by dot-path."""
    from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata

    meta = {
        "_raw_description": {
            "Predictor": {
                "models": [
                    {"Type": "brise.MultiArmedBandit"},
                    {"Type": "brise.TreeParzenEstimator"},
                ]
            }
        }
    }

    # List element access via index
    assert ExperimentMetadata.get(meta, "Predictor.models.0.Type") == "brise.MultiArmedBandit"
    assert ExperimentMetadata.get(meta, "Predictor.models.1.Type") == "brise.TreeParzenEstimator"
