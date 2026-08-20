from dataclasses import replace
from pathlib import Path

from credit_portfolio_analytics.cli import main
from credit_portfolio_analytics.config import ProjectConfig
from credit_portfolio_analytics.database import build_warehouse
from credit_portfolio_analytics.reporting import render_executive_report, write_executive_report

ROOT = Path(__file__).parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "loans_sample.csv"


def test_render_and_write_executive_report(tmp_path: Path) -> None:
    base = ProjectConfig.load(ROOT / "config" / "project.toml")
    config = replace(
        base,
        warehouse_path=tmp_path / "test.duckdb",
        powerbi_output_dir=tmp_path / "powerbi",
    )
    build_warehouse(config, source_path=FIXTURE)

    report = render_executive_report(config, minimum_segment_loans=1)

    assert "# Executive credit risk review" in report
    assert "6 accepted-loan records" in report
    assert "Expected-loss sensitivity" in report
    assert "Interpretation limits" in report

    output = write_executive_report(
        config,
        tmp_path / "report.md",
        minimum_segment_loans=1,
    )
    assert output.read_text(encoding="utf-8") == report


def test_report_cli_does_not_require_an_input_argument(tmp_path: Path) -> None:
    base = ProjectConfig.load(ROOT / "config" / "project.toml")
    warehouse = tmp_path / "test.duckdb"
    build_config = replace(
        base,
        warehouse_path=warehouse,
        powerbi_output_dir=tmp_path / "powerbi",
    )
    build_warehouse(build_config, source_path=FIXTURE)
    config_path = tmp_path / "project.toml"
    config_path.write_text(
        (ROOT / "config" / "project.toml")
        .read_text(encoding="utf-8")
        .replace(
            'warehouse_path = "data/processed/credit_portfolio.duckdb"',
            f'warehouse_path = "{warehouse}"',
        ),
        encoding="utf-8",
    )
    output = tmp_path / "cli-report.md"

    result = main(
        [
            "--config",
            str(config_path),
            "report",
            "--output",
            str(output),
            "--minimum-segment-loans",
            "1",
        ]
    )

    assert result == 0
    assert output.exists()
