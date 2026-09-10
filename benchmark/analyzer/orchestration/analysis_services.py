import logging
import os
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from analyzer.data_pipeline.experiment_metadata import ExperimentMetadata

logger = logging.getLogger(__name__)


@dataclass
class ObjectivePartitionService:
    extractor: Any

    def partition(self, configured: List[str], experiments: List[Any]) -> Dict[str, List[Any]]:
        if self._is_instance_mode(configured, experiments):
            return self._partition_by_problem_instance(configured, experiments)

        if configured:
            result_keys = configured
        else:
            result_keys = sorted(self.extractor.discover_objectives(experiments))
            logger.info(f"Discovered result keys: {result_keys}")

        return {key: experiments for key in result_keys}

    @staticmethod
    def resolve_result_key(objective: str, experiments: List[Any]) -> str:
        if not experiments:
            return objective
        sample_configs = getattr(experiments[0], 'measured_configurations', [])[:1]
        if sample_configs:
            keys = set(getattr(sample_configs[0], 'results', {}).keys())
            if objective not in keys and 'objective' in keys:
                return 'objective'
        return objective

    @staticmethod
    def _is_instance_mode(configured: List[str], experiments: List[Any]) -> bool:
        if not configured:
            return False
        sample_instances = {
            ExperimentMetadata.extract(exp).get("problem_instance", "")
            for exp in experiments[:20]
        }
        return any(obj in sample_instances for obj in configured)

    @staticmethod
    def _partition_by_problem_instance(configured: List[str], experiments: List[Any]) -> Dict[str, List[Any]]:
        partitions: Dict[str, List[Any]] = {obj: [] for obj in configured}
        for exp in experiments:
            inst = ExperimentMetadata.extract(exp).get("problem_instance", "")
            if inst in partitions:
                partitions[inst].append(exp)
        return {k: v for k, v in partitions.items() if v}


class ComparativeTableService:
    @staticmethod
    def build(
        comparative_results: Dict[str, List[Any]],
        table_config: Any,
        is_minimizing_fn: Optional[Any] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        from analyzer.data_pipeline import ExperimentParser

        parser = ExperimentParser()
        comparative_tables: Dict[str, List[Dict[str, Any]]] = {}

        for objective, comparison_list in comparative_results.items():
            if not comparison_list:
                continue

            rows: List[Dict[str, Any]] = []
            for result in comparison_list:
                row: Dict[str, Any] = {}

                if not table_config or table_config.experiment:
                    row['Experiment'] = result.display_name or result.experiment_name
                if not table_config or table_config.baseline:
                    row['Baseline'] = parser.build_display_name(result.baseline_type)
                if (not table_config or table_config.final_regret) and result.final_regret is not None:
                    row['Final Regret'] = f"{result.final_regret:.6f}"

                if not table_config or table_config.relative_improvement:
                    if result.relative_improvement is not None:
                        row['RI (Objective)'] = f"{result.relative_improvement:.4f}"
                    if result.relative_improvement_time is not None:
                        row['RI (Time)'] = f"{result.relative_improvement_time:.4f}"
                    if result.relative_improvement_iterations is not None:
                        row['RI (Iterations)'] = f"{result.relative_improvement_iterations:.4f}"

                if result.converged_at_iteration is not None and (not table_config or table_config.converged_at_iteration):
                    row['Converged at Iter'] = result.converged_at_iteration

                minimize = is_minimizing_fn(objective) if is_minimizing_fn else True
                if result.experiment_trajectory and (not table_config or table_config.experiment_best):
                    exp_best = min(result.experiment_trajectory) if minimize else max(result.experiment_trajectory)
                    row['Experiment Best'] = f"{exp_best:.6f}"
                if result.baseline_trajectory and (not table_config or table_config.baseline_best):
                    base_best = min(result.baseline_trajectory) if minimize else max(result.baseline_trajectory)
                    row['Baseline Best'] = f"{base_best:.6f}"

                rows.append(row)

            if rows:
                comparative_tables[objective] = rows

        return comparative_tables


class ExportService:
    NUMERIC_COLUMNS = ['Initial', 'Final best', 'Absolute improvement', 'Improvement %']

    def save_csv_files(
        self,
        tables_by_objective: Dict[str, List[Dict[str, Any]]],
        output_csv: str,
        comparative_tables_by_objective: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> Tuple[Dict[str, str], Dict[str, str], Optional[str]]:
        logger.info("Saving CSV files...")
        output_dir = os.path.dirname(output_csv) or '.'
        os.makedirs(output_dir, exist_ok=True)

        self._save_combined_csv(tables_by_objective, output_csv)
        csv_files = self._save_per_objective_csvs(
            tables_by_objective,
            output_dir,
            filename_template="benchmark_objective_{objective}.csv",
        )
        comparative_csv_files: Dict[str, str] = {}
        if comparative_tables_by_objective:
            comparative_csv_files = self._save_per_objective_csvs(
                comparative_tables_by_objective,
                output_dir,
                filename_template="benchmark_comparative_{objective}.csv",
            )

        zip_file = self._create_zip_archive(
            output_csv,
            list(csv_files.values()) + list(comparative_csv_files.values()),
            output_dir,
        )
        return csv_files, comparative_csv_files, zip_file

    def _save_combined_csv(self, tables_by_objective: Dict[str, List[Dict[str, Any]]], output_csv: str):
        all_rows = [row for rows in tables_by_objective.values() for row in rows]
        df = pd.DataFrame(all_rows)
        self._round_numeric_columns(df)
        df.to_csv(output_csv, index=False)

    def _save_per_objective_csvs(
        self,
        tables_by_objective: Dict[str, List[Dict[str, Any]]],
        output_dir: str,
        filename_template: str,
    ) -> Dict[str, str]:
        csv_files: Dict[str, str] = {}
        for objective, rows in tables_by_objective.items():
            df = pd.DataFrame(rows)
            self._round_numeric_columns(df)
            filename = filename_template.format(objective=objective)
            df.to_csv(os.path.join(output_dir, filename), index=False)
            csv_files[objective] = filename
        return csv_files

    @classmethod
    def _round_numeric_columns(cls, df: pd.DataFrame):
        for col in cls.NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').round(6)

    @staticmethod
    def _create_zip_archive(output_csv: str, csv_filenames: List[str], output_dir: str) -> Optional[str]:
        logger.info("Creating ZIP archive...")
        zip_filename = os.path.join(output_dir, "benchmark_all_tables.zip")

        try:
            with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                zf.write(output_csv, arcname=os.path.basename(output_csv))
                for filename in csv_filenames:
                    zf.write(os.path.join(output_dir, filename), arcname=filename)
            return os.path.basename(zip_filename)
        except Exception as e:
            logger.warning(f"ZIP creation failed: {e}")
            return None

