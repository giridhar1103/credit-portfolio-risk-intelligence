from pathlib import Path

from credit_portfolio_analytics.config import ProjectConfig


def test_project_config_loads() -> None:
    path = Path(__file__).parents[1] / "config" / "project.toml"
    config = ProjectConfig.load(path)

    assert config.snapshot_date.isoformat() == "2018-12-31"
    assert config.source_observation_date.isoformat() == "2019-04-01"
    assert config.fallback_lgd == 0.60
    assert config.lgd_smoothing_exposure == 1_000_000
    assert [scenario.key for scenario in config.scenarios] == ["baseline", "moderate", "severe"]
