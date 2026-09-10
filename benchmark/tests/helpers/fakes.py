from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class FakeMeasuredConfiguration:
    results: Dict[str, Any]
    is_enabled: bool = True
    iteration_timestamp: Optional[datetime] = None
    hyperparameters: Optional[Dict[str, Any]] = None


@dataclass
class FakeExperiment:
    name: str
    measured_configurations: List[FakeMeasuredConfiguration]
    description: Optional[Dict[str, Any]] = None
    ed_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


def create_fake_experiment(
    name: str,
    values: List[Dict[str, Any]],
    is_enabled: Optional[List[bool]] = None,
    start_time: Optional[datetime] = None,
    description: Optional[Dict[str, Any]] = None,
) -> FakeExperiment:
    start = start_time or datetime(2024, 1, 1, 12, 0, 0)
    flags = is_enabled or [True] * len(values)
    measured = [
        FakeMeasuredConfiguration(
            results=v,
            is_enabled=flags[i],
            iteration_timestamp=start + timedelta(seconds=i * 10),
            hyperparameters={"hp": i},
        )
        for i, v in enumerate(values)
    ]
    return FakeExperiment(
        name=name,
        measured_configurations=measured,
        description=description or {},
        ed_id=f"{name}_id",
        start_time=start,
        end_time=start + timedelta(seconds=max(1, len(values) * 10)),
    )

