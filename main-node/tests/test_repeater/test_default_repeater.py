from repeater.default_repeater import DefaultRepeater

def test_decision_function():
    WS = "WS"
    def_repeater = DefaultRepeater(WS)
    result = def_repeater.decision_function(def_repeater.history, (1200, 32)) #history is empty
    result_exp = False
    assert result_exp == result


# TODO - make history with 10+ elements (WSClient)