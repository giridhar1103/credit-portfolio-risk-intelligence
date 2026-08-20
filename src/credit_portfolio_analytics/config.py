"""Typed project configuration loaded from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Scenario:
    key: str
    display_name: str
    pd_multiplier: float


@dataclass(frozen=True)
class ProjectConfig:
    repo_root: Path
    snapshot_date: date
    source_observation_date: date
    raw_loans_csv: Path
    warehouse_path: Path
    powerbi_output_dir: Path
    default_statuses: tuple[str, ...]
    non_default_statuses: tuple[str, ...]
    delinquent_statuses: tuple[str, ...]
    charged_off_statuses: tuple[str, ...]
    open_statuses: tuple[str, ...]
    fallback_lgd: float
    pd_smoothing_observations: int
    lgd_smoothing_exposure: float
    scenarios: tuple[Scenario, ...]

    @classmethod
    def load(cls, path: Path | str) -> ProjectConfig:
        config_path = Path(path).resolve()
        with config_path.open("rb") as handle:
            raw = tomllib.load(handle)

        repo_root = config_path.parent.parent
        project = raw["project"]
        targets = raw["targets"]
        loss = raw["expected_loss"]

        scenarios = tuple(
            Scenario(
                key=key,
                display_name=value["display_name"],
                pd_multiplier=float(value["pd_multiplier"]),
            )
            for key, value in raw["scenarios"].items()
        )

        if not scenarios or scenarios[0].key != "baseline":
            raise ValueError("The first configured scenario must be 'baseline'.")
        if not 0 < float(loss["fallback_lgd"]) <= 1:
            raise ValueError("Fallback LGD must be greater than 0 and no more than 1.")
        if float(loss["lgd_smoothing_exposure"]) <= 0:
            raise ValueError("LGD smoothing exposure must be positive.")
        if any(item.pd_multiplier <= 0 for item in scenarios):
            raise ValueError("Every scenario PD multiplier must be positive.")

        return cls(
            repo_root=repo_root,
            snapshot_date=date.fromisoformat(project["snapshot_date"]),
            source_observation_date=date.fromisoformat(project["source_observation_date"]),
            raw_loans_csv=repo_root / project["raw_loans_csv"],
            warehouse_path=repo_root / project["warehouse_path"],
            powerbi_output_dir=repo_root / project["powerbi_output_dir"],
            default_statuses=tuple(targets["default_statuses"]),
            non_default_statuses=tuple(targets["non_default_statuses"]),
            delinquent_statuses=tuple(targets["delinquent_statuses"]),
            charged_off_statuses=tuple(targets["charged_off_statuses"]),
            open_statuses=tuple(targets["open_statuses"]),
            fallback_lgd=float(loss["fallback_lgd"]),
            pd_smoothing_observations=int(loss["pd_smoothing_observations"]),
            lgd_smoothing_exposure=float(loss["lgd_smoothing_exposure"]),
            scenarios=scenarios,
        )


def default_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "project.toml"
