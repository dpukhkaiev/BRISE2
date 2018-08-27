from repeater.default_repeater import DefaultRepeater

EXPERIMENTS = {
        "TaskName": "energy_consumption",
        "FileToRead": "Radix-500mio.csv",
        "ResultStructure": ["frequency", "threads", "energy"],
        "ResultDataTypes": ["float", "int", "float"],
        "RepeaterDecisionFunction": "student_deviation",
        "MaxRepeatsOfExperiment": 4
}
WS = "should be WS"


def test_decision_function():
    def_repeater = DefaultRepeater(WS, EXPERIMENTS)
    result = def_repeater.decision_function(def_repeater.history, (1200, 32)) #history is empty
    assert result is False


# TODO - make history with 10+ elements (WSClient)