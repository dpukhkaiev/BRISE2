from reconfiguration.effector import Effector

class ReconfigurationExecutor():
    """Handle reconfiguration requests with the use of effectors"""

    def __init__(self):
        self.effectors = {}

        self.update_effectors()

    def update_effectors(self, do_cleanup:bool=True):
        """Load all effectors in the `effectors`dict. Key is the variability point and the value is the instance of the effector"""
        self.effectors = {}

        # Remove all unused instances
        if do_cleanup:
            Effector.cleanup()

        # Init the effectors dict
        for effector in Effector.get_all():
            vp = effector.vp
            if vp in self.effectors:
                self.effectors[vp].append(effector)
                continue
            
            self.effectors[vp] = [effector]

    def change(self, variability_point:str, new_description:tuple, full_description:tuple, identifiers:None|list):
        """Change the component for the given variability point according to the ``new_description``"""
        if variability_point not in self.effectors:
            # Go to the "upper" VP for surrogate and optimizer
            if "_" in variability_point and variability_point.startswith("Surrogate") or variability_point.startswith("Optimizer"):
                variability_point = variability_point.split("_")[0] # Use coarse grained VP
                # Give a list of all surrogates or optimizers as the description
                new_description = self._get_descriptions(variability_point, full_description, identifiers)
            else:
                raise KeyError("No effector for the variability point " + variability_point + " found!")
        
        for e in self.effectors[variability_point]:
            # Check for identifiers
            if identifiers is not None and len(identifiers) != 0: # Allow all identifiers if none are specified
                if len(e.identifiers) == 0 or set(e.identifiers) != set(identifiers): # (all identifiers must match IF any identifiers are specified)
                    continue

            e.change(full_description if e.full_description else new_description)

    def _get_descriptions(self, vp:str, experiment_description:dict, identifiers:list|None = None):
        """Return a list with the description of all variants for the given variability point in the given model"""
        descriptions = []

        model_name = "Model"

        # Get identifier for model_name
        if identifiers is not None:
            for i in identifiers:
                if i.startswith("Model"):
                    model_name = i
                    break

        model_description = experiment_description["ConfigurationSelection"]["Predictor"][model_name]
        for key, description in model_description.items():
            if key.startswith(vp):
                descriptions.append(description)

        return descriptions