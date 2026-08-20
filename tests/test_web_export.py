import json
from dataclasses import replace
from pathlib import Path

from credit_portfolio_analytics.config import ProjectConfig
from credit_portfolio_analytics.database import build_warehouse
from credit_portfolio_analytics.web_export import build_dashboard_bundle, write_dashboard_bundle

ROOT = Path(__file__).parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "loans_sample.csv"


def test_dashboard_bundle_contains_only_reconciled_marts(tmp_path: Path) -> None:
    base = ProjectConfig.load(ROOT / "config" / "project.toml")
    config = replace(
        base,
        warehouse_path=tmp_path / "test.duckdb",
        powerbi_output_dir=tmp_path / "powerbi",
    )
    build_warehouse(config, source_path=FIXTURE)

    bundle = build_dashboard_bundle(config)

    assert bundle["schema_version"] == "1.0.0"
    assert bundle["quality"]["warehouse_reconciled"] is True
    assert bundle["tables"]["executive_summary"][0]["matured_loans"] == 3
    assert bundle["tables"]["open_book"][0]["outstanding_exposure"] == 29_000
    assert len(bundle["tables"]["expected_loss_summary"]) == 3

    output = write_dashboard_bundle(config, tmp_path / "dashboard.json")
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["quality"]["reconciliation_check_count"] == 6
