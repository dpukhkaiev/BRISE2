"""
Waffle Selenium Validator

Drives the Waffle wizard UI (Chrome) for each PairwiseConfig produced by
pairwise_generator.py.  For every config it:
  1. Loads the appropriate context WFL file into the UI
  2. Walks through each step, filling inputs based on the pairwise
     feature selections and parsed min/max and enum constraints
  3. Downloads the configured product JSON if the config is valid
  4. Logs invalid configs to invalid_configs.log

Usage:
    python3 selenium_validator.py
    # Waffle UI must be running at localhost:8000

Requirements:
    selenium
    chromedriver
"""

# Set to True to print step-by-step debug output to stdout
DEBUG_MODE = False

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from pairwise_generator import PairwiseConfig, generate_pairwise
from wfl_parser_textx import WflParserTextX


# Paths / URLs

_HERE = Path(__file__).parent
OUTPUT_DIR = _HERE / "output_configs"
LOG_FILE = _HERE / "invalid_configs.log"
WAFFLE_URL = "http://127.0.0.1:8000/wizard/initialize/"


# Artificial upper caps for attributes that have only a lower bound in the WFL
# These are the values entered into number fields

ARTIFICIAL_CAPS: Dict[str, Any] = {
    # MOEA
    "Generations": 10,
    "PopulationSize": 70, # must be in [35,70,126,…] AND >= 63
    # RepetitionManager
    "MaxFailedTasksPerConfiguration": 3,
    "MaxTasksPerConfiguration": 3,
    "MinTasksPerUnderperformingConfiguration": 1,
    # StopConditions
    "MaxBadConfigurations": 5,
    "MaxConfigsWithoutImprovement": 5,
    "MaxConfigs": 10,
    "MaxRunTime": 10,
    # TransferLearning
    "MinNumberOfSamples": 5,
    "NumberOfSimilarExperiments": 3,
    "OldNewConfigsRatio": 10.0,
    "RatioMax": 10.0,
    "TimeToBuildModelThreshold": 10.0,
    "Value": 5, # Finite RecommendationGranularity [Value >= 1]
    # Sampling
    "Seed": 1,
    # CandidateSelector
    "NumberOfPoints": 1,
    # Search space parameter bounds.
    # Waffle asks for Lower/Upper/Default when defining hyperparameter ranges
    "Upper": 10,
    # General
    "RepetitionPeriod": 5,
    # AcceptableErrorBased RepetitionManager:
    # WFL constraint: MaxAcceptableError > BaseAcceptableError.
    # Both have parser-found max=99.99, so we cap them to ensure ordering holds.
    "BaseAcceptableError": 1.0,   # small baseline
    "MaxAcceptableError": 50.0,   # must be > BaseAcceptableError
    # Surrogate-specific parameters
    "n_estimators": 10,
    "max_iter": 100,
    "n_restarts_optimizer": 2,
    "C": 10.0,
    "CFloat": 10.0,
    "GammaFloat": 1.0,
    "bandwidth_factor": 5.0,
    "min_bandwidth": 0.1,
    # MeanShift clustering (AdaptiveQuantity):
    # WFL: [if BandwidthType == "Fixed" then quantile == -1]
    # We always use BandwidthType="Fixed" (ENUM_PREFERENCES), so quantile must be exactly -1.
    "quantile": -1.0,
}


# Preferred values for string/enum text fields (first valid option).
# Used when the UI shows a text input for a constrained string attribute

# ConfigurationTransformers required by each context's hyperparameter types.
# The Waffle wizard presents these as checkboxes in an OR group.
# When the search space contains a given HP type, the matching transformer
# MUST be selected — otherwise BRISE passes raw values to sklearn and crashes.
# This implements the missing WFL constraints at the validator level.
# Unconditional feature replacements: if a pairwise config would select a
# feature value listed as a key, replace it with the corresponding value.
# EnergyValidator is designed for special energy optimization tasks and
# hardcodes results["energy"] — our test configs use Y1/Y2 objectives,
# so EnergyValidator always crashes with KeyError. Use MockValidator instead.
FEATURE_REPLACEMENTS: Dict[str, str] = {
    "EnergyValidator": "MockValidator",
}


CONTEXT_REQUIRED_TRANSFORMERS: Dict[str, List[str]] = {
    "2-float":    [],
    "float-nom":  ["NominalTransformer"],
    "all-types":  ["NominalTransformer", "OrdinalTransformer"],
}

CONTEXT_SEARCH_SPACE_BOUNDS: Dict[str, Dict[str, Any]] = {
    "float-nom": {"Lower": -100.5, "Upper": 457.98, "Default": -7.0},
}

# MOEA algorithms that are single-objective only (MultiObjective = False in WFL).
# Valid with SurrogateTypes that scalarize/split objectives (Scalar, Compositional,
# DynamicCompositional) because the optimizer sees nobj=1.
# Invalid with Pure/Portfolio because the optimizer sees nobj>1.
SINGLE_OBJECTIVE_ALGORITHMS: set = {
    "GACO", "GWO", "BEE_COLONY", "DE", "SEA", "SGA",
    "SADE", "DE1220", "CMAES", "PSO", "PSO_GEN",
}

# MOEA algorithms that are multi-objective only (MultiObjective = True in WFL).
# Valid with SurrogateTypes that keep multiple objectives (Pure, Portfolio).
# Invalid with Scalar/Compositional/DynamicCompositional because nobj=1.
MULTI_OBJECTIVE_ALGORITHMS: set = {
    "MOEAD", "NSGA2", "MACO", "MOEAD_GEN", "NSPSO",
}

# SurrogateTypes that keep multiple objectives -> require MO algorithms only.
MO_SURROGATE_TYPES: set = {"Pure", "Portfolio", "DynamicCompositional"}

# SurrogateTypes that reduce to 1 objective -> require SO algorithms only.
SO_SURROGATE_TYPES: set = {"Scalar", "Compositional"}


ENUM_PREFERENCES: Dict[str, str] = {
    "BandwidthType": "Fixed",
    "CType": "std",
    "GammaType": "scale",
    "ThresholdType": "Soft",
    "TimeUnit": "seconds",
    "activation": "relu",
    "kernel": "rbf",
    "solver": "adam",
}


# WFL constraint incompatibilities between feature values
# when a feature value has at least one "trigger" selected in the config,
# that value is skipped during filling to avoid an unavoidable conflict
#
# format: { value_to_skip: [trigger_features, ...] }
#
# example: NSGA2 requires PopulationSize % 4 == 0, but MOEAD/MOEAD_GEN require
# populationSize in {35, 70, 126, ...}, no integer satisfies both simultaneously,
# so NSGA2 is skipped whenever MOEAD or MOEAD_GEN is also selected.

WFL_CONFLICTS: Dict[str, List[str]] = {
    # MOEA algorithms, PopulationSize incompatibilities
    # NSGA2 requires PopulationSize % 4 == 0; MOEAD/MOEAD_GEN require in {35,70,126,...}
    # No integer satisfies both simultaneously -> skip NSGA2 when MOEAD is present
    "NSGA2": ["MOEAD", "MOEAD_GEN"],

    # SurrogateType = Pure excludes most surrogates, only GaussianProcessRegressor and
    # ModelMock are compatible with Pure, skip all incompatible surrogates when Pure
    # is selected in the config
    "LinearRegression": ["Pure"],
    "SupportVectorRegression": ["Pure"],
    "GradientBoostingRegressor": ["Pure"],
    "BayesianRidgeRegression": ["Pure"],
    "MultiArmedBandit": ["Pure"],
    "TreeParzenEstimator": ["Pure", "DynamicCompositional", "Portfolio"],
    "MultiLayerPerceptronRegressor": ["Pure"],

    # SurrogateType = Portfolio incompatibilities:
    # BestMultiPointProposal (BMP) is excluded by Portfolio
    # TreeParzenEstimator is excluded by Portfolio (already covered above)
    "BestMultiPointProposal": ["Portfolio"],

    # Symmetric rules: skip these SurrogateType options when incompatible features
    # are already selected (prevents wrong fallback choices in xor SurrogateType groups).
    # Portfolio excludes BMP -> skip Portfolio when BMP is selected.
    "Portfolio": ["BestMultiPointProposal"],
    # Pure excludes most surrogates -> skip Pure when any of those surrogates is selected.
    "Pure": ["LinearRegression", "SupportVectorRegression", "GradientBoostingRegressor",
             "BayesianRidgeRegression", "MultiArmedBandit", "MultiLayerPerceptronRegressor"],

    # MultiArmedBandit excludes all ConfigurationTransformers (BinaryEncoder et al.)
    # When MAB is selected, skip all CT sub-features to avoid the excludes constraint.
    "BinaryEncoder": ["MultiArmedBandit"],
    "SklearnBinaryEncoder": ["MultiArmedBandit"],
    "SklearnOrdinalEncoder": ["MultiArmedBandit"],
    "SklearnIntMinMaxScaler": ["MultiArmedBandit"],
    "SklearnFloatMinMaxScaler": ["MultiArmedBandit"],
    # MAB also requires fcard.ConfigurationTransformers == 0 — skip the transformer
    # container features so no CT instance is activated.
    "NominalTransformer": ["MultiArmedBandit"],
    "OrdinalTransformer": ["MultiArmedBandit"],
    "IntegerTransformer": ["MultiArmedBandit"],
    "FloatTransformer": ["MultiArmedBandit"],
    "MersenneTwister": ["FewShotMultiTask"],
}

# Hardcoded defaults for non-enum free-text fields.
# "Name" is handled dynamically (unique per StopCondition instance).
TEXT_DEFAULTS: Dict[str, str] = {
    "Expression": "StopCondition1",
    "Default": "Default param",
    # SVR gamma must match GammaType; since ENUM_PREFERENCES picks "scale", gamma="scale"
    "gamma": "scale",
    # MLP hidden_layer_sizes is an integerArray field; Waffle validates it as an integer
    "hidden_layer_sizes": "100",
}



# Module-level helper

def _last_segment(dotted_name: str) -> str:
    """Return the last segment after the final dot
    """
    return dotted_name.rsplit(".", 1)[-1]



# Main class

class WaffleSeleniumValidator:
    """Automates Waffle for all pairwise configurations"""

    def __init__(
        self,
        grammar_path: str,
        wfl_path: str,
        models_dir: str,
        output_dir: Path = OUTPUT_DIR,
        waffle_url: str = WAFFLE_URL,
    ):
        self.models_dir = Path(models_dir)
        self.output_dir = output_dir
        self.waffle_url = waffle_url
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Parse WFL to get typed min/max bounds and enum constraints
        parser = WflParserTextX(grammar_path, wfl_path)
        self._min_max_raw = parser.parse_min_max()

        # Merge parser output with artificial caps
        self._min_max = self._build_min_max()

        # Set up simple file logger
        logging.basicConfig(
            filename=str(LOG_FILE),
            level=logging.INFO,
            format="%(asctime)s  %(message)s",
        )


    def validate_all(self, configs: List[PairwiseConfig]) -> List[PairwiseConfig]:
        """Drive the wizard for every config, returns valid configs only"""
        valid: List[PairwiseConfig] = []
        for cfg in configs:
            print(f"[{cfg.index:2d}] context={cfg.context_variant:<18}", end="  ", flush=True)
            success = self._run_wizard(cfg)
            if success:
                print("valid")
                valid.append(cfg)
            else:
                print("invalid")
                logging.info(f"INVALID  index={cfg.index}  context={cfg.context_variant}")
        return valid


    def _dbg(self, msg: str) -> None:
        """Print debug message to stdout if DEBUG_MODE is enabled"""
        if DEBUG_MODE:
            print(f"DBG: {msg}", flush=True)

    def _run_wizard(self, cfg: PairwiseConfig) -> bool:
        """Open a fresh Chrome session, walk the wizard, download if valid"""
        driver = self._make_driver()
        try:
            wait = WebDriverWait(driver, timeout=30, poll_frequency=0.5)

            nextstep_loc = (By.XPATH, "//form//input[@value='Next step']")
            download_loc = (By.XPATH, "//form//input[@value='Download configured product']")

            # Load page and submit WFL
            driver.get(self.waffle_url)
            wfl_content = self._get_wfl_content(cfg.context_variant)
            wait.until(EC.visibility_of_element_located((By.NAME, "model_field")))
            driver.execute_script(
                "arguments[0].value = arguments[1];",
                driver.find_element(By.ID, "textarea"),
                wfl_content,
            )
            wait.until(EC.element_to_be_clickable((By.NAME, "Manual")))
            driver.find_element(By.NAME, "Manual").click()
            wait.until(EC.visibility_of_element_located(nextstep_loc))
            self._dbg("WFL loaded, wizard started")

            # Config-specific min/max adjustments
            # Note: Level fields are no longer set here; _build_level_map() assigns them
            # dynamically by nesting depth so that consecutive Level values 0, 1, 2, …
            # are produced, matching BRISE's models_types[level] index expectations.
            local_mm = dict(self._min_max)

            # PopulationSize: MOEAD/MOEAD_GEN require value in {35,70,126,...} AND >= 63  use 70.
            # NSGA2 requires % 4 == 0 (satisfied by 72).
            # When MOEAD+NSGA2 appear together, NSGA2 is skipped via WFL_CONFLICTS
            # (no single value satisfies both constraints), so the MOEAD cap applies.
            if self._matches_selection("MOEAD", cfg) or self._matches_selection("MOEAD_GEN", cfg):
                local_mm["PopulationSize"] = {"min": None, "max": 70, "type": "integer"}
            else:
                local_mm["PopulationSize"] = {"min": None, "max": 72, "type": "integer"}

            # For multi-objective contexts the WFL forces fcard.MultiObjectiveHandling = 1
            # Submitting 0 causes Waffle to silently activate MOH (via the constraint)
            # but skip the SurrogateType selection step, defaulting to Pure.
            # Pre-set MultiObjectiveHandling = 1 so the SurrogateType step IS shown.
            if "-mo" in cfg.context_variant:
                local_mm["MultiObjectiveHandling"] = {"min": None, "max": 1, "type": "integer"}

            for prefix, bounds in CONTEXT_SEARCH_SPACE_BOUNDS.items():
                if cfg.context_variant.startswith(prefix):
                    for attr, val in bounds.items():
                        local_mm[attr] = {"min": None, "max": val, "type": "float"}
                    break

            name_counter = [1]
            step_num = 0

            #Main wizard loop
            while True:
                step_num += 1

                # check for wizard completion
                if driver.find_elements(*download_loc):
                    self._dbg(f"step {step_num}: DOWNLOAD button found, wizard complete")
                    break

                # check: next step must exist
                if not driver.find_elements(*nextstep_loc):
                    self._dbg(f"step {step_num}: NO nextstep and NO download -> abort")
                    logging.info(f"NO_NEXTSTEP  step={step_num}  index={cfg.index}  context={cfg.context_variant}")
                    return False

                # check for constraint validation error
                for alert in driver.find_elements(By.XPATH, "//div[@role='alert']"):
                    if "Constraint validation error" in alert.text:
                        self._dbg(f"step {step_num}: CONSTRAINT ERROR: {alert.text[:500]}")
                        logging.info(f"CONSTRAINT  step={step_num}  index={cfg.index}  context={cfg.context_variant}")
                        return False

                # determine input type on this step
                req_types = {
                    el.get_attribute("type")
                    for el in driver.find_elements(By.XPATH, "//form//input[@required='']")
                }
                # Always detect radio/checkbox/select regardless of required number/text inputs.
                # A Waffle step can show both required number Fcard inputs AND non-required
                # XOR radio buttons (e.g. SurrogateType radios on the MultiObjectiveHandling
                # Fcard step) The old guard 'if not req_types' caused those radios to be
                # missed when req_types already contained "number", leaving SurrogateType
                # unselected -> Waffle defaulted to Pure ->constraint error
                if driver.find_elements(By.XPATH, "//form//input[@type='radio']"):
                    req_types.add("radio")
                if driver.find_elements(By.XPATH, "//form//input[@type='checkbox']"):
                    req_types.add("checkbox")
                # Also detect <select> elements (Waffle renders xor groups as dropdowns)
                if driver.find_elements(By.XPATH, "//form//select"):
                    req_types.add("select")

                self._dbg(f"step {step_num}: req_types={req_types}")

                # Fill/click current step inputs
                # A single step can carry multiple input types simultaneously
                # (e.g. a Waffle_Constraint_Group_ step shows both the Structure
                # XOR radio buttons AND the Level integer fields at once)
                # Handle every present type independently
                if "number" in req_types:
                    self._fill_numbers(driver, cfg, local_mm)
                if "text" in req_types:
                    self._fill_texts(driver, name_counter)
                if "radio" in req_types:
                    self._click_radios(driver, cfg)
                if "checkbox" in req_types:
                    self._click_checkboxes(driver, cfg)
                if "select" in req_types:
                    self._pick_selects(driver, cfg)
                # Always fill non-required Fcard inputs to prevent Waffle from
                # defaulting to wrong values for sub-features of disabled parents
                # (e.g. SurrogateType.Portfolio inside disabled MultiObjectiveHandling)
                self._fill_optional_fcards(driver, cfg, local_mm)
                # (empty req_types = no inputs on this step, just click Next)

                # Click Next and wait for page navigation to complete
                next_btn = driver.find_element(*nextstep_loc)
                wait.until(EC.element_to_be_clickable(next_btn))
                next_btn.click()
                self._dbg(f"step {step_num}: clicked Next")

                # Wait for old button to go stale (confirms DOM replaced)
                # If it times out, the browser blocked form submission because a
                # required field was left empty, this config is invalid
                try:
                    wait.until(EC.staleness_of(next_btn))
                    self._dbg(f"step {step_num}: staleness OK")
                except TimeoutException:
                    self._dbg(f"step {step_num}: STALENESS TIMEOUT (browser blocked form)")
                    logging.info(f"STALENESS_TIMEOUT  step={step_num}  index={cfg.index}  context={cfg.context_variant}")
                    return False

                # Wait for new page: next step, download, or alert must appear
                try:
                    wait.until(lambda d: (
                        d.find_elements(*nextstep_loc)
                        or d.find_elements(*download_loc)
                        or d.find_elements(By.XPATH, "//div[@role='alert']")
                    ))
                except TimeoutException:
                    url = driver.current_url
                    # Extract traceback from Django debug page
                    full_src = driver.page_source
                    # Try to find the key error line in the Django debug HTML
                    tb_match = re.search(
                        r'<(pre|td)[^>]*exception_value[^>]*>(.+?)</(pre|td)>',
                        full_src, re.DOTALL
                    )
                    tb_text = tb_match.group(2).strip() if tb_match else full_src[300:800].replace("\n", " ")
                    # Also try title
                    title_match = re.search(r'<title>(.+?)</title>', full_src[:500])
                    title = title_match.group(1).strip() if title_match else "?"
                    self._dbg(f"step {step_num}: LAMBDA TIMEOUT — url={url}")
                    self._dbg(f"  page title: {title}")
                    self._dbg(f"  error: {tb_text[:300]}")
                    logging.info(
                        f"LAMBDA_TIMEOUT  step={step_num}  url={url}  title={title!r}  "
                        f"index={cfg.index}  context={cfg.context_variant}"
                    )
                    return False

                # Determine what appeared
                if DEBUG_MODE:
                    if driver.find_elements(*nextstep_loc):
                        self._dbg(f"step {step_num}: -> nextstep appeared")
                    elif driver.find_elements(*download_loc):
                        self._dbg(f"step {step_num}: -> download appeared")
                    else:
                        alert_els = driver.find_elements(By.XPATH, "//div[@role='alert']")
                        alert_text = alert_els[0].text[:80] if alert_els else "?"
                        self._dbg(f"step {step_num}: -> alert: {alert_text}")

                # Small pause to let the DOM finish rendering form inputs
                time.sleep(0.3)

            # Download
            files_before = set(self.output_dir.iterdir())
            wait.until(EC.element_to_be_clickable(download_loc))
            driver.find_element(*download_loc).click()
            deadline = time.time() + 10
            new_file: Optional[Path] = None
            while time.time() < deadline:
                time.sleep(0.5)
                files_after = set(self.output_dir.iterdir())
                new_files = files_after - files_before
                done = [f for f in new_files if f.suffix != ".crdownload"]
                if done:
                    new_file = done[0]
                    break
            if new_file:
                target = self.output_dir / f"config_{cfg.index}_{cfg.context_variant}.json"
                new_file.rename(target)
                self._fix_empty_weights(target)
            return True

        except Exception as exc:
            logging.info(f"ERROR index={cfg.index}  context={cfg.context_variant}  {exc}")
            return False

        finally:
            driver.quit()


    # Private: input fillers

    def _build_level_map(self, driver) -> Dict[str, int]:
        """Compute a path -> consecutive-level mapping for all Level fields visible on the current wizard step

        sort all Level field paths by segment count (a proxy for nesting depth
        in the search space), then assign consecutive integers to distinct depth groups.
        Example for all-types-so:
          Context.SearchSpace.N0.Level            (4 segments) -> level 0
          Context.SearchSpace.N0.N01.F1.Level     (6 segments) -> level 1
          Context.SearchSpace.N0.N02.N1.Level     (6 segments) -> level 1

        This assumes all Level fields for a given search space appear in the same wizard
        step (Waffle groups them in the SearchSpace Constraint_Group step)
        """
        level_fields: list[tuple[int, str]] = []
        for el in driver.find_elements(By.XPATH, "//form//input[@required=''][@type='number']"):
            raw_name = el.get_attribute("name")
            dotted = raw_name.split("-", 1)[-1] if "-" in raw_name else raw_name
            if _last_segment(dotted) == "Level":
                depth = len(dotted.split("."))
                level_fields.append((depth, dotted))

        # Map each unique depth to a consecutive integer, smallest depth -> 0
        unique_depths = sorted({d for d, _ in level_fields})
        depth_to_level = {d: i for i, d in enumerate(unique_depths)}
        return {path: depth_to_level[depth] for depth, path in level_fields}

    def _fill_numbers(self, driver, cfg, local_mm):
        # Pre-compute depth-based Level assignments for all Level fields on this step.
        # For Flat structure the WFL enforces Level==0 for every HP; use 0 directly.
        # For Hierarchical, assign consecutive integers by nesting depth (0, 1, …)
        is_flat = self._matches_selection("Flat", cfg)
        level_map = {} if is_flat else self._build_level_map(driver)
        required_transformers = self._get_required_transformers(cfg)

        for el in driver.find_elements(By.XPATH, "//form//input[@required=''][@type='number']"):
            raw_name = el.get_attribute("name")
            # Strip the step prefix "N-"
            dotted = raw_name.split("-", 1)[-1] if "-" in raw_name else raw_name
            attr = _last_segment(dotted)

            if attr == "Level":
                # For Flat, WFL forces Level==0, for Hierarchical, use depth map
                val = "0" if is_flat else str(level_map.get(dotted, 0))
                self._dbg(f"  fill_number: {dotted} -> val={val!r} ({'flat=0' if is_flat else 'depth-derived'})")
            else:
                # Pass the feature path for Fcard fields so _get_fill_value can use
                # the .None sentinel approach (prevents false positives from descendants)
                # Normalize Model_N -> Model so indexed paths match pairwise selections.
                feature_path = re.sub(r"\.Model_\d+", ".Model", dotted[len("Fcard."):]) if dotted.startswith("Fcard.") else None
                val = self._get_fill_value(attr, cfg, local_mm, feature_path)
                # For Fcard fields, ensure we never send below the wizard-advertised minimum
                # A '+' cardinality feature (mandatory, min=1) would crash the Waffle server
                # with an IndexError if we send 0 (2-tuple cardinality error vs 3-tuple
                # constraint error: views.py always does res[2])
                if feature_path is not None and val == "0":
                    fcard_min = self._get_fcard_min(el)
                    if fcard_min > 0:
                        val = str(fcard_min)
                        self._dbg(f"  fcard_min override: {dotted} min={fcard_min}")
                # Force ConfigurationTransformers fcard to 1 for both Surrogate and
                # Optimizer when the context requires NominalTransformer/OrdinalTransformer.
                if attr == "ConfigurationTransformers" and required_transformers and val == "0":
                    val = "1"
                self._dbg(f"  fill_number: {dotted} -> val={val!r}")

            el.clear()
            el.send_keys(val)

    def _fill_optional_fcards(self, driver, cfg, local_mm):
        """Fill non-required Fcard number inputs.

        Waffle always renders ALL wizard steps regardless of parent fcard values.
        Sub-feature Fcard inputs for disabled parents (e.g. SurrogateType.Portfolio
        inside disabled MultiObjectiveHandling) are shown but not @required,
        Without explicit values these inputs may keep an HTML default that
        accidentally activates a conflicting feature (e.g. Portfolio),
        set them to 0 unless cfg.selections indicates they should be enabled
        """
        required_transformers = self._get_required_transformers(cfg)
        for el in driver.find_elements(
            By.XPATH, "//form//input[@type='number'][not(@required='')]"
        ):
            raw_name = el.get_attribute("name")
            dotted = raw_name.split("-", 1)[-1] if "-" in raw_name else raw_name
            if not dotted.startswith("Fcard."):
                continue  # only touch Fcard fields
            attr = _last_segment(dotted)
            feature_path = re.sub(r"\.Model_\d+", ".Model", dotted[len("Fcard."):])
            val = self._get_fill_value(attr, cfg, local_mm, feature_path)
            # Force ConfigurationTransformers fcard to 1 for both Surrogate and
            # Optimizer when the context requires NominalTransformer/OrdinalTransformer.
            # Without this, the Surrogate's CT fcard defaults to 0 and BRISE receives
            # raw nominal/ordinal strings it cannot convert to float.
            if attr == "ConfigurationTransformers" and required_transformers and val == "0":
                val = "1"
            self._dbg(f"  fill_opt_fcard: {dotted} -> val={val!r}")
            el.clear()
            el.send_keys(val)

    def _fill_texts(self, driver, name_counter):
        for el in driver.find_elements(By.XPATH, "//form//input[@required=''][@type='text']"):
            attr = _last_segment(el.get_attribute("name"))
            val = self._get_text_value(attr, name_counter)
            el.clear()
            el.send_keys(val)

    def _click_radios(self, driver, cfg):
        # Iterate all radio buttons
        # option with required=''
        # every non-first choice (e.g. Hierarchical when Flat is first)
        clicked_any = False
        all_radios = driver.find_elements(By.XPATH, "//form//input[@type='radio']")
        # Build index of radios by value for replacement lookups
        radios_by_val: Dict[str, Any] = {}
        for el in all_radios:
            v = el.get_attribute("value") or ""
            if v:
                radios_by_val[v] = el
        for el in all_radios:
            val = el.get_attribute("value") or ""
            name = el.get_attribute("name") or ""
            if bool(val) and self._is_conflicting(val, cfg):
                self._dbg(f"  radio: {val!r} skipped (WFL conflict)")
                continue
            # Check for unconditional replacements (e.g. EnergyValidator → MockValidator)
            if bool(val) and val in FEATURE_REPLACEMENTS:
                if self._matches_selection(val, cfg):
                    replacement = FEATURE_REPLACEMENTS[val]
                    rep_el = radios_by_val.get(replacement)
                    if rep_el:
                        self._dbg(f"  radio: {val!r} replaced by {replacement!r} (FEATURE_REPLACEMENTS)")
                        rep_el.click()
                        clicked_any = True
                    else:
                        self._dbg(f"  radio: {val!r} replacement {replacement!r} not found on page")
                else:
                    self._dbg(f"  radio: {val!r} skipped (in FEATURE_REPLACEMENTS, not selected)")
                continue
            match = bool(val) and self._matches_selection(val, cfg)
            self._dbg(f"  radio: name={name!r} val={val!r} -> {'CLICK' if match else 'skip'}")
            if match:
                el.click()
                clicked_any = True
        # Fallback: if nothing matched, click the first non-conflicting required
        # radio in each distinct radio group so HTML5 validation doesn't block form
        # submission, with multiple Model_N groups on one step there can be several
        # independent required groups that each need exactly one selection.
        if not clicked_any:
            req = driver.find_elements(By.XPATH, "//form//input[@required=''][@type='radio']")
            seen_names: set = set()
            for el in req:
                name = el.get_attribute("name") or ""
                if name in seen_names:
                    continue
                val = el.get_attribute("value") or ""
                if self._is_conflicting(val, cfg) or val in FEATURE_REPLACEMENTS:
                    continue
                self._dbg(f"  radio fallback: clicking first required radio val={val!r} name={name!r}")
                el.click()
                seen_names.add(name)

    def _get_required_transformers(self, cfg) -> set:
        """Return transformer checkbox values that MUST be selected for this
        config's context HP types (e.g. OrdinalTransformer for all-types)."""
        for prefix, transformers in CONTEXT_REQUIRED_TRANSFORMERS.items():
            if cfg.context_variant.startswith(prefix):
                return set(transformers)
        return set()

    def _click_checkboxes(self, driver, cfg):
        # Collect all checkboxes, click any whose value matches a pairwise selection
        # or is a required transformer for this context's HP types
        required_transformers = self._get_required_transformers(cfg)
        all_cbs = driver.find_elements(By.XPATH, "//form//input[@type='checkbox']")
        clicked_groups: set = set()  # track which name-groups got a click
        for el in all_cbs:
            val = el.get_attribute("value") or ""
            name = el.get_attribute("name") or ""
            if bool(val) and self._is_conflicting(val, cfg):
                self._dbg(f"  checkbox: {val!r} skipped (WFL conflict)")
                continue
            if bool(val) and self._is_algorithm_incompatible(val, cfg):
                continue
            forced = val in required_transformers
            match = bool(val) and (self._matches_selection(val, cfg) or forced)
            tag = ""
            if forced and not self._matches_selection(val, cfg):
                tag = " (forced: context requires this transformer)"
            self._dbg(f"  checkbox: name={name!r} val={val!r} -> {'CLICK' if match else 'skip'}{tag}")
            if match:
                el.click()
                clicked_groups.add(name)
        # Fallback: OR groups require at least one selection. For each distinct
        # name-group that had no click, select the first non-conflicting checkbox.
        # This handles multi-model steps where Model_0 and Model_1 each have
        # their own OR group that independently needs at least one selection.
        groups: dict = {}
        for el in all_cbs:
            name = el.get_attribute("name") or ""
            if name not in groups:
                groups[name] = []
            groups[name].append(el)
        for name, elements in groups.items():
            if name in clicked_groups:
                continue
            eligible = [el for el in elements
                        if not self._is_conflicting(el.get_attribute("value") or "", cfg)
                        and not self._is_algorithm_incompatible(el.get_attribute("value") or "", cfg)]
            target = eligible[0] if eligible else elements[0]
            self._dbg(f"  checkbox fallback: clicking {target.get_attribute('value')!r} "
                      f"for group {name!r}")
            target.click()

    def _pick_selects(self, driver, cfg):
        """Handle <select> dropdowns (Waffle renders xor groups as dropdowns).

        For each <select> on the form, find the <option> whose value matches
        cfg.selections and select it, ff no option matches, leave the current
        selection unchanged (avoids accidentally committing a wrong default)
        Conflicting options are skipped via WFL_CONFLICTS
        """
        from selenium.webdriver.support.select import Select
        for sel_el in driver.find_elements(By.XPATH, "//form//select"):
            sel_obj = Select(sel_el)
            options = sel_el.find_elements(By.TAG_NAME, "option")
            picked = False
            for opt in options:
                val = opt.get_attribute("value") or ""
                if not val or val == "---------":
                    continue
                if self._is_conflicting(val, cfg):
                    self._dbg(f"  select: {val!r} skipped (WFL conflict)")
                    continue
                if self._matches_selection(val, cfg):
                    self._dbg(f"  select: {val!r} -> PICK")
                    sel_obj.select_by_value(val)
                    picked = True
                    break
            if not picked:
                # No match found, log but leave default (don't force a wrong value)
                cur = sel_obj.first_selected_option.get_attribute("value") if options else "?"
                self._dbg(f"  select: no match -> keeping default {cur!r}")

    def _is_algorithm_incompatible(self, val: str, cfg: "PairwiseConfig") -> bool:
        """Return True if an algorithm is incompatible with the selected SurrogateType.

        Pure/Portfolio keep all objectives (nobj>1) -> only MO algorithms allowed.
        Scalar/Compositional/DynamicCompositional reduce to 1 objective -> only SO algorithms.
        In single-objective contexts, MO algorithms are always invalid.
        """
        is_so_context = "-so" in cfg.context_variant
        is_mo_context = "-mo" in cfg.context_variant
        uses_mo_surrogate = any(
            self._matches_selection(st, cfg) for st in MO_SURROGATE_TYPES
        )
        uses_so_surrogate = any(
            self._matches_selection(st, cfg) for st in SO_SURROGATE_TYPES
        )

        if val in SINGLE_OBJECTIVE_ALGORITHMS and is_mo_context and uses_mo_surrogate:
            self._dbg(f"  checkbox: {val!r} skipped (SO algorithm with Pure/Portfolio)")
            return True
        if val in MULTI_OBJECTIVE_ALGORITHMS and is_mo_context and uses_so_surrogate:
            self._dbg(f"  checkbox: {val!r} skipped (MO algorithm with Scalar/Compositional/DynamicCompositional)")
            return True
        if val in MULTI_OBJECTIVE_ALGORITHMS and is_so_context:
            self._dbg(f"  checkbox: {val!r} skipped (MO algorithm in SO context)")
            return True
        return False

    def _is_conflicting(self, val: str, cfg: "PairwiseConfig") -> bool:
        """Return True if val should be skipped because a conflicting feature is selected.

        Uses WFL_CONFLICTS: if any trigger feature for val is present in cfg,
        selecting val would cause an unavoidable WFL constraint violation
        """
        triggers = WFL_CONFLICTS.get(val)
        if not triggers:
            pass
        elif any(self._matches_selection(t, cfg, check_ancestors=True) for t in triggers):
            return True
        if val == "DynamicModelsRecommendation" and cfg.context_variant.startswith("all-types") \
                and self._matches_selection("Hierarchical", cfg):
            return True
        return False

    def _matches_selection(self, val: str, cfg: "PairwiseConfig",
                           check_ancestors: bool = False) -> bool:
        """Return True if val appears as any path segment of a selected (non-None) feature

        Checks three positions to avoid false-substring matches:
          - final segment:  sel ends with '.val'
          - exact match:    sel == val
          - middle segment: '.val.' appears anywhere in sel
            (e.g. NominalTransformer matches
             '...ConfigurationTransformers.NominalTransformer.BinaryEncoder')

        check_ancestors=True: additionally require that no ancestor path segment
        is a '.None' sentinel.  Used only in _is_conflicting so that a feature
        inside a disabled parent (e.g. Pure under MultiObjectiveHandling.None) is
        not treated as an active conflict trigger.  Direct click matching uses
        check_ancestors=False so that features like DynamicCompositional are still
        clicked even when listed under a .None parent (which can happen when the
        WFL forces the parent active regardless of the pairwise selection).
        """
        suffix = f".{val}"
        inner  = f".{val}."
        for sel in cfg.selections:
            if sel.endswith(".None"):
                continue
            if not (sel.endswith(suffix) or sel == val or inner in sel):
                continue
            if check_ancestors:
                parts = sel.split(".")
                if any(
                    ".".join(parts[:i]) + ".None" in cfg.selections
                    for i in range(1, len(parts))
                ):
                    continue
            return True
        return False
    
    # Private: value helpers

    def _get_fill_value(
        self, attr: str, cfg: PairwiseConfig, local_mm: Dict,
        feature_path: Optional[str] = None,
    ) -> str:
        """Return the string value to enter for a number field.

        feature_path (optional): the full dotted feature path extracted from an
        Fcard field name (e.g. 'TransferLearning.ModelRecommendation'), when
        provided, a precise .None-sentinel approach is used to avoid false
        positives from descendant selections that contain the feature name as a
        substring, without it (Value fields), a last-segment endswith check is
        used instead
        """
        if attr in local_mm:
            if local_mm[attr]["max"] is not None:
                return str(local_mm[attr]["max"])
            if local_mm[attr]["min"] is not None:
                return str(local_mm[attr]["min"])

        if feature_path is not None:
            # Fcard field: the feature is NOT selected if its .None sentinel is
            # present; it is selected if the path itself or any direct descendant
            # appears without .None.
            if f"{feature_path}.None" in cfg.selections:
                return "0"
            fp_prefix = feature_path + "."
            if any(
                (sel == feature_path or sel.startswith(fp_prefix))
                and not sel.endswith(".None")
                for sel in cfg.selections
            ):
                return "1"
            return "0"

        # Value (attribute) field: match by last path segment
        suffix = f".{attr}"
        if any(
            (sel == attr or sel.endswith(suffix)) and not sel.endswith(".None")
            for sel in cfg.selections
        ):
            return "1"
        return "0"

    def _get_text_value(self, attr: str, name_counter: list) -> str:
        """Return the string value to enter for a text field."""
        if attr == "Name":
            val = f"SC{name_counter[0]}"
            name_counter[0] += 1
            return val
        if attr in ENUM_PREFERENCES:
            return ENUM_PREFERENCES[attr]
        return TEXT_DEFAULTS.get(attr, "value1")

    def _get_fcard_min(self, el) -> int:
        """Read minimum allowed Fcard value from the wizard form label.

        The Waffle wizard renders labels as:
            "Feature Cardinality for feature X. Allowed values: Y"
        where Y is one of:
            "1..inf"  ('+' cardinality -> min=1)
            "0..inf"  ('*' cardinality -> min=0)
            "0 or 1"  ('?' cardinality -> min=0)
            "<n>"     (exact numeric cardinality -> min=n)

        Returns the minimum integer, or 0 on any parse failure.
        """
        try:
            parent = el.find_element(
                By.XPATH, "ancestor::div[contains(@class,'form-group')]"
            )
            text = parent.text
            m = re.search(r'Allowed values:\s*(\S+)', text)
            if m:
                first_token = m.group(1)        # e.g. "1..inf", "0..inf", "0"
                first_num = first_token.split('..')[0]  # e.g. "1", "0", "0"
                return int(first_num)
        except Exception:
            pass
        return 0

    def _get_wfl_content(self, context_variant: str) -> str:
        """Read the WFL context file for the given variant"""
        return (self.models_dir / f"{context_variant}.wfl").read_text()

    def _fix_empty_weights(self, path: Path) -> None:
        """Replace empty Weights ({}) with a list of 1s matching the objective count.
        """
        data = json.loads(path.read_text())
        objectives = data.get("Context", {}).get("TaskConfiguration", {}).get("Objectives", {})
        n_obj = len(objectives)
        if n_obj == 0:
            return

        def _patch(node):
            if isinstance(node, dict):
                if "WeightedSum" in node and isinstance(node["WeightedSum"], dict):
                    ws = node["WeightedSum"]
                    if "Weights" in ws and ws["Weights"] in ({}, []):
                        ws["Weights"] = [1] * n_obj
                        self._dbg(f"  patched Weights -> {ws['Weights']}")
                for v in node.values():
                    _patch(v)

        _patch(data)
        path.write_text(json.dumps(data, indent=4) + "\n")

    def _make_driver(self) -> webdriver.Chrome:
        """Create a Chrome WebDriver with download directory configured."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("prefs", {
            "download.default_directory": str(self.output_dir.resolve()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
        })
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)


    # Private: min/max builder

    def _build_min_max(self) -> Dict[str, Dict]:
        """Merge WFL-parsed bounds with ARTIFICIAL_CAPS

        ARTIFICIAL_CAPS always act as a ceiling: when the parser already found a
        max, we use min(parser_max, cap).  This ensures ordering constraints like
        'MaxAcceptableError > BaseAcceptableError' are not violated by sending
        both attributes at their WFL-derived ceiling of 99.99
        """
        result: Dict[str, Dict] = {}

        for attr, constraints in self._min_max_raw.items():
            max_val = constraints["max"]
            if attr in ARTIFICIAL_CAPS:
                cap = ARTIFICIAL_CAPS[attr]
                max_val = min(max_val, cap) if max_val is not None else cap
            result[attr] = {
                "min": constraints["min"],
                "max": max_val,
                "type": constraints["type"],
            }

        # Add caps for attributes not found in WFL at all
        for attr, cap in ARTIFICIAL_CAPS.items():
            if attr not in result:
                result[attr] = {"min": None, "max": cap, "type": "unknown"}

        return result


# CLI entry point

if __name__ == "__main__":
    import sys

    grammar = "grammar.tx"
    wfl = "base.wfl"
    models = "WaffleTestingModels"

    # Args: [limit] [start]
    #   python3 selenium_validator.py 25 -> run config 25
    #   python3 selenium_validator.py 23 22 -> run configs 22 to 22 (single debug)
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    print("Generating pairwise configurations...")
    configs = generate_pairwise(grammar, wfl)
    print(f"  {len(configs)} configurations to validate\n")

    if limit or start:
        configs = configs[start:limit]
        print(f"  (running configs {start}..{(limit or len(configs)) - 1} for debug)\n")

    validator = WaffleSeleniumValidator(
        grammar_path=grammar,
        wfl_path=wfl,
        models_dir=models,
    )

    valid_configs = validator.validate_all(configs)

    print(f"\n{'='*50}")
    print(f"Valid   : {len(valid_configs)}/{len(configs)}")
    print(f"Invalid : {len(configs) - len(valid_configs)}/{len(configs)}")
    print(f"Output  : {OUTPUT_DIR}/")
    print(f"Log     : {LOG_FILE}")
