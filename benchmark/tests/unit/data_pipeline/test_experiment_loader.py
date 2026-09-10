import pickle
from types import SimpleNamespace

from analyzer.data_pipeline.experiment_loader import ExperimentLoader


def _dump_exp(path, name, start_time):
    exp = SimpleNamespace(name=name, start_time=start_time, measured_configurations=[])
    with open(path, "wb") as handle:
        pickle.dump(exp, handle)


def test_load_all_experiments_sorts_by_start_time_and_sets_source_filename(tmp_path):
    _dump_exp(tmp_path / "b.pkl", "exp_b", 20)
    _dump_exp(tmp_path / "a.pkl", "exp_a", 10)

    loader = ExperimentLoader(str(tmp_path))
    loaded = loader.load_all_experiments()

    assert [e.name for e in loaded] == ["exp_a", "exp_b"]
    assert loaded[0]._source_filename == "a.pkl"


def test_group_experiments_removes_repetition_suffixes_for_new_and_legacy_names():
    loader = ExperimentLoader("unused")
    experiments = [
        SimpleNamespace(name="exp_task_model_sampler_cfg_sc_0", measured_configurations=[]),
        SimpleNamespace(name="exp_task_model_sampler_cfg_sc_1", measured_configurations=[]),
        SimpleNamespace(name="exp_tsp_hh_hash(0)", measured_configurations=[]),
        SimpleNamespace(name="exp_tsp_hh_hash(0)(1)", measured_configurations=[]),
    ]

    groups = loader.group_experiments(experiments)

    assert set(groups.keys()) == {"exp_task_model_sampler_cfg_sc", "exp_tsp_hh_hash"}
    assert len(groups["exp_task_model_sampler_cfg_sc"]) == 2
    assert len(groups["exp_tsp_hh_hash"]) == 2

