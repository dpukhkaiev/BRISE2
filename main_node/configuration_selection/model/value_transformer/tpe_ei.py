# BSD 3-Clause License

# Copyright (c) 2017-2018, ML4AAD
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pandas as pd
import numpy as np
from typing import Dict

from configuration_selection.model.value_transformer.acquisition_function_abs import AcquisitionFunction


class TpeEi(AcquisitionFunction):
    def __init__(self, value_transformer_description: Dict, objectives: Dict):
        super().__init__(value_transformer_description, objectives)
        self.objective = self.objectives[list(objectives.keys())[0]]
        self.is_minimization = self.objective["Minimization"]

    def transform(self, objective_function_values: pd.DataFrame) -> pd.DataFrame:
        names = objective_function_values.columns.tolist()
        good = None
        bad = None
        for name in names:
            if "probability_good" in name:
                good = objective_function_values[name][0]  # value of pd.Series
                continue
            if "probability_bad" in name:
                bad = objective_function_values[name][0]
        if good is None or bad is None:
            raise ValueError("Check Tree Parzen Estimator implementation for output columns!")

        if self.is_minimization:
            ratio = bad / good
        else:
            ratio = good / bad

        # Applies if prediction is infinity.
        if not np.isfinite(ratio):
            # right now, this happens because a KDE does not contain all values for a categorical parameter
            # this cannot be fixed with the statsmodels KDE, so for now, we are just going to evaluate this one
            # if the good_kde has a finite value, i.e. there is no config with that value in the bad kde, so it shouldn't be terrible.
            if np.isfinite(good):
                ratio = good

        result = pd.DataFrame([ratio], columns=["ratio"])

        return result
