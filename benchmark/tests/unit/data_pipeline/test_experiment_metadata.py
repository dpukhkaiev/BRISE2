"""Tests for ExperimentMetadata variant detection — both schema versions."""
import pytest
from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata


def _make_meta(model_types_list, mh_type, legacy_model_type=""):
    """Build a minimal meta dict as _compute_hhpc_variant expects."""
    return {
        "model_types_list": model_types_list,
        "mh_type": mh_type,
        "legacy_model_type": legacy_model_type,
    }


# ---------------------------------------------------------------------------
# New schema (Predictor.models list) — unchanged behaviour
# ---------------------------------------------------------------------------

class TestNewSchemaVariants:
    def test_s_tpe(self):
        meta = _make_meta(["ModelMock", "TreeParzenEstimator"], "py.SA")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "S-TPE"

    def test_s_brr(self):
        meta = _make_meta(["ModelMock", "BayesianRidge"], "py.ES")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "S-BRR"

    def test_framab_h_tpe(self):
        meta = _make_meta(["MultiArmedBandit", "TreeParzenEstimator"], "HH-PC")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "FRAMAB-H-TPE"

    def test_framab_h_brr(self):
        meta = _make_meta(["MultiArmedBandit", "BayesianRidge"], "HH-PC")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "FRAMAB-H-BRR"

    def test_brr_h_tpe(self):
        meta = _make_meta(["BayesianRidge", "TreeParzenEstimator"], "HH-PC")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "BRR-H-TPE"

    def test_brr_h_brr(self):
        meta = _make_meta(["BayesianRidge", "BayesianRidge"], "HH-PC")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "BRR-H-BRR"

    def test_baseline_modelmock_only_returns_empty(self):
        meta = _make_meta(["ModelMock"], "HH-PC")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == ""

    def test_new_schema_ignores_legacy_field(self):
        # When Predictor.models is present the legacy_model_type must not interfere.
        meta = _make_meta(["ModelMock", "TreeParzenEstimator"], "py.SA",
                          legacy_model_type="brr")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "S-TPE"

    # ------------------------------------------------------------------
    # Order-independence: reversed model list must give the same result
    # ------------------------------------------------------------------

    def test_s_tpe_reversed_order(self):
        meta = _make_meta(["TreeParzenEstimator", "ModelMock"], "py.SA")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "S-TPE"

    def test_s_brr_reversed_order(self):
        meta = _make_meta(["BayesianRidge", "ModelMock"], "py.ES")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "S-BRR"

    def test_framab_h_tpe_reversed_order(self):
        meta = _make_meta(["TreeParzenEstimator", "MultiArmedBandit"], "HH-PC")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "FRAMAB-H-TPE"

    def test_brr_h_tpe_reversed_order(self):
        meta = _make_meta(["TreeParzenEstimator", "BayesianRidge"], "HH-PC")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "BRR-H-TPE"


# ---------------------------------------------------------------------------
# Legacy schema (ModelConfiguration.ModelType, no Predictor.models)
# sparse_pc_and_hh_pc experiments — new behaviour added in this change.
# ---------------------------------------------------------------------------

class TestLegacySchemaVariants:
    """The old BRISE format stored the surrogate as a single string.
    "BO"  = BayesianRidge-based surrogate in old BRISE naming → S-BRR
    "brr" = TreeParzenEstimator-like surrogate in old BRISE naming → S-TPE
    (counter-intuitive; verified against hand-crafted report)
    All modes (HH-PC, j.ES, py.ES, py.SA) yield the same S-* label because
    every experiment in that folder uses a flat/sparse search space.
    """

    @pytest.mark.parametrize("mh_type", ["HH-PC", "j.ES", "py.ES", "py.SA"])
    def test_bo_maps_to_s_brr_for_all_mh_modes(self, mh_type):
        meta = _make_meta([], mh_type, legacy_model_type="BO")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "S-BRR"

    @pytest.mark.parametrize("mh_type", ["HH-PC", "j.ES", "py.ES", "py.SA"])
    def test_brr_maps_to_s_tpe_for_all_mh_modes(self, mh_type):
        meta = _make_meta([], mh_type, legacy_model_type="brr")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == "S-TPE"

    def test_unknown_legacy_model_type_returns_empty(self):
        meta = _make_meta([], "HH-PC", legacy_model_type="unknown")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == ""

    def test_empty_legacy_model_type_returns_empty(self):
        meta = _make_meta([], "py.SA", legacy_model_type="")
        assert ExperimentMetadata._compute_hhpc_variant(meta) == ""
