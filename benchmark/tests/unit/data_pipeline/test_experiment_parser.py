from analyzer.data_pipeline.experiment_parser import ExperimentParser
from tests.helpers.fakes import create_fake_experiment


def test_parse_features_with_test_case_and_index_suffix():
    parser = ExperimentParser()
    name = "exp_taskA_modelB_sobol_quantitybased_timebased_test_case_2_wo_dch_3"

    features = parser.parse_features(name)

    assert features["Task"] == "taskA"
    assert features["Model"] == "modelB"
    assert features["TestCase"] == 2
    assert features["Index"] == 3


def test_parse_features_from_experiment_prefers_non_placeholder_name_strategy():
    parser = ExperimentParser()
    exp = create_fake_experiment(
        name="exp_task_model_sampler_quantitybased_timebased_test_case_0_1",
        values=[{"Y1": 10.0}],
        description={
            "TaskConfiguration": {
                "TaskName": "my-task",
                "Scenario": {
                    "Hyperparameters": "tuned",
                    "TestCase": 77,
                },
            },
            "StopCondition": {"Name": "time-based"},
        },
    )

    features = parser.parse_features_from_experiment(exp)

    assert features["Task"] == "my-task"
    assert features["ConfigurationStrategy"] == "quantitybased"
    assert features["StopCondition"] == "time-based"
    assert features["TestCase"] == 0


def test_build_display_name_for_baseline_and_test_case_variants():
    parser = ExperimentParser()

    assert parser.build_display_name("baseline_grid-search") == "grid-search"
    assert parser.build_display_name("exp_t_m_s_c_sc_baseline_random-search_2") == "random-search"
    assert parser.build_display_name("exp_a_b_c_d_e_test_case_9_1") == "test_case_9"


