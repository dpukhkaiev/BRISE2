from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


def _flatten_dict(d: Any, prefix: str = "", sep: str = ".") -> Dict[str, Any]:
    """Recursively flatten a nested dict into dot-path keys (stops at lists and non-dict values)."""
    result = {}
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{prefix}{sep}{k}" if prefix else k
            if isinstance(v, dict):
                result.update(_flatten_dict(v, new_key, sep))
            else:
                result[new_key] = v
    return result


def _nested_get(d: Any, parts: List[str]) -> Any:
    """Walk a nested structure (dicts and lists) using a list of path parts."""
    current = d
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


class ExperimentMetadata:
    """Extracts a flat, dot-addressable metadata dict from an experiment."""

    @staticmethod
    def extract(exp: Any) -> Dict[str, Any]:
        source_filename = getattr(exp, "_source_filename", "") or ""
        meta: Dict[str, Any] = {
            "filename": source_filename,
            "exp_name": getattr(exp, "name", "") or "",
            "exp_id": getattr(exp, "id", "") or "",
            "num_measured": len(getattr(exp, "measured_configurations", [])),
            "repetition": ExperimentMetadata._parse_repetition(source_filename),
        }

        desc = getattr(exp, "description", None)
        if isinstance(desc, dict):
            meta.update(_flatten_dict(desc, prefix="description"))
            meta["_raw_description"] = desc
        elif desc is not None:
            logger.warning(
                "Experiment '%s' has non-dict description of type '%s'",
                meta.get("exp_name") or meta.get("exp_id") or "unknown",
                type(desc).__name__,
            )

        ExperimentMetadata._add_aliases(meta, exp)
        return meta

    @staticmethod
    def _add_aliases(meta: Dict[str, Any], exp: Any) -> None:
        desc_dict = meta.get("_raw_description") or {}

        # --- Simple direct aliases ---
        task_name = meta.get("description.TaskConfiguration.TaskName", "")
        meta["task_name"] = str(task_name) if task_name else ""

        instance_path = (
            meta.get("description.TaskConfiguration.Scenario.problem_initialization_parameters.instance")
            or meta.get("description.DomainDescription.instance")
            or ""
        )
        meta["problem_instance_path"] = str(instance_path)
        meta["problem_instance"] = os.path.basename(str(instance_path)) if instance_path else ""

        hp = meta.get("description.TaskConfiguration.Scenario.Hyperparameters", "")
        meta["hyperparams_mode"] = str(hp) if hp else ""

        datafile = meta.get("description.DomainDescription.DataFile", "")
        meta["domain_datafile"] = str(datafile)
        meta["mh_type"] = ExperimentMetadata._parse_mh_type(str(datafile))

        # --- Model types from Predictor.models list (new schema) ---
        predictor = desc_dict.get("Predictor", {}) if isinstance(desc_dict.get("Predictor"), dict) else {}
        models = predictor.get("models", []) if isinstance(predictor.get("models"), list) else []
        meta["model_types_list"] = [
            m.get("Type", "").split(".")[-1]
            for m in models if isinstance(m, dict)
        ]

        # --- Legacy schema fallback: ModelConfiguration.ModelType (old BRISE format) ---
        # Old experiments store a single surrogate name ("BO" for TPE-like, "brr" for BRR)
        # under ModelConfiguration instead of a Predictor.models list.
        mc = desc_dict.get("ModelConfiguration")
        legacy_mt = mc.get("ModelType", "") if isinstance(mc, dict) else ""
        meta["legacy_model_type"] = legacy_mt

        # --- Hyperparameter values of first measured configuration ---
        cfgs = getattr(exp, "measured_configurations", [])
        meta["first_param_values"] = {}
        if cfgs:
            hyperparams = getattr(cfgs[0], "hyperparameters", None)
            if isinstance(hyperparams, dict):
                meta["first_param_values"] = dict(hyperparams)
            elif hyperparams is not None:
                try:
                    meta["first_param_values"] = dict(hyperparams)
                except (TypeError, ValueError):
                    pass

        # --- Computed group variant ---
        meta["hhpc_variant"] = ExperimentMetadata._compute_hhpc_variant(meta)

    @staticmethod
    def _parse_repetition(filename: str) -> int:
        """Parse the repetition index of a run from its serialized filename.

        BRISE avoids filename collisions when the same experiment is re-run by
        appending ``(0)``, ``(0)(1)``, … to the dump name. These suffixes are
        *not* cumulative — each file is an independent repetition. The base file
        (no suffix) is repetition 0; ``...(N)`` is repetition ``N + 1``.

        Also handles the new-style trailing ``_N`` convention. Returns 0 when no
        repetition marker is present.
        """
        name = filename[:-4] if filename.endswith(".pkl") else filename
        legacy = re.findall(r"\((\d+)\)", name)
        if legacy:
            return int(legacy[-1]) + 1
        new_style = re.search(r"_(\d+)$", name)
        if new_style:
            return int(new_style.group(1))
        return 0

    @staticmethod
    def _parse_mh_type(datafile: str) -> str:
        b = os.path.basename(datafile).lower()
        if b.startswith("hh") or "hhdata" in b:
            return "HH-PC"
        if "pysa" in b or ("py" in b and "sa" in b):
            return "py.SA"
        if "pyes" in b or ("jmetalpy" in b and "es" in b):
            return "py.ES"
        if "jes" in b or ("jmetal" in b and "es" in b):
            return "j.ES"
        return os.path.splitext(os.path.basename(datafile))[0] if datafile else ""

    @staticmethod
    def _compute_hhpc_variant(meta: Dict[str, Any]) -> str:
        """Derive a group label from model types and domain type.

        Maps experiment model combinations to the six benchmark groups:
        S-TPE, S-BRR, FRAMAB-H-TPE, FRAMAB-H-BRR, BRR-H-TPE, BRR-H-BRR.
        Returns "" for default/baseline experiments that don't fit any group.

        Handles two BRISE config schemas:
        - New schema (full_benchmark): surrogate read from ``Predictor.models[*].Type``
          list (``model_types_list``).
        - Legacy schema (sparse_pc_and_hh_pc): surrogate stored as a single string in
          ``ModelConfiguration.ModelType`` (``legacy_model_type``).  The mapping is
          ``"BO"`` → TPE (Bayesian/TPE surrogate) and ``"brr"`` → BRR (Bayesian Ridge
          Regression surrogate).
        """
        model_types: List[str] = meta.get("model_types_list", [])
        is_hh = meta.get("mh_type", "") == "HH-PC"

        # --- New-schema path (order-independent: check all model names) ---
        if model_types:
            names = [m.lower() for m in model_types]
            has_mab = any("multiarmedbandit" in n for n in names)
            has_tpe = any("treeparzen" in n for n in names)
            has_brr = any("bayesianridge" in n for n in names)
            has_mock = any("modelmock" in n for n in names)

            lower = "TPE" if has_tpe else ("BRR" if has_brr else "")

            if not is_hh:
                if has_mock and lower:
                    return f"S-{lower}"
                return ""
            # Hierarchical (HH-PC)
            if has_mab:
                return f"FRAMAB-H-{lower}" if lower else ""
            if has_brr:
                # Upper level is BRR; lower level is TPE if present, else BRR
                lower_h = "TPE" if has_tpe else "BRR"
                return f"BRR-H-{lower_h}"
            return ""

        # --- Legacy-schema fallback (no Predictor.models) ---
        # "BO"  = BayesianRidge-based surrogate in the old BRISE format → S-BRR
        # "brr" = TreeParzenEstimator-like surrogate in the old BRISE format → S-TPE
        # (counter-intuitive naming in the legacy config — verified against hand-crafted report)
        legacy_mt = meta.get("legacy_model_type", "").lower()
        if legacy_mt == "bo":
            legacy_lower = "BRR"
        elif legacy_mt == "brr":
            legacy_lower = "TPE"
        else:
            return ""

        # All legacy experiments with a recognised surrogate are sparse (flat
        # search space), regardless of the MH/HH domain description used.
        return f"S-{legacy_lower}"

    @staticmethod
    def get(meta: Dict[str, Any], path: str) -> Any:
        """Retrieve a value from the metadata dict by dot-path.

        Lookup order:
          1. Top-level aliases:  ``"problem_instance"``, ``"hhpc_variant"`` …
          2. Full dot-paths:     ``"description.TaskConfiguration.TaskName"``
          3. Sub-path shortcut:  ``"TaskConfiguration.TaskName"``
             (prepends ``"description."`` automatically)
          4. Hyperparameter leaf: ``"first_param_values.some_param"``
          5. Raw nested traversal of the original description dict,
             supporting list indices (e.g. ``"Predictor.models.0.Type"``).
        """
        if path in meta:
            return meta[path]

        desc_path = "description." + path
        if desc_path in meta:
            return meta[desc_path]

        if path.startswith("first_param_values."):
            key = path[len("first_param_values."):]
            return meta.get("first_param_values", {}).get(key)

        # Walk the raw description using the path (supports nested dicts and list indices)
        raw_desc = meta.get("_raw_description")
        if raw_desc is not None:
            parts = path.split(".")
            # Try path directly in raw description
            value = _nested_get(raw_desc, parts)
            if value is not None:
                return value
            # Also strip a leading "description." prefix if present
            if parts and parts[0] == "description":
                value = _nested_get(raw_desc, parts[1:])
                if value is not None:
                    return value

        return None
