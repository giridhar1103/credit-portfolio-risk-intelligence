"""DuckDB warehouse build and Power BI export functions."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .config import ProjectConfig

if TYPE_CHECKING:
    import duckdb


def _sql_literal(value: str | Path) -> str:
    return str(value).replace("'", "''")


def _sql_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{_sql_literal(value)}'" for value in values)


def _render_sql(path: Path, replacements: dict[str, str]) -> str:
    sql = path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        sql = sql.replace("{{" + key + "}}", value)
    unresolved = [part.split("}}", 1)[0] for part in sql.split("{{")[1:] if "}}" in part]
    if unresolved:
        raise ValueError(f"Unresolved SQL template variables in {path.name}: {unresolved}")
    return sql


def _create_scenario_dimension(
    connection: duckdb.DuckDBPyConnection, config: ProjectConfig
) -> None:
    connection.execute(
        """
        CREATE OR REPLACE TABLE dim_scenario (
            scenario_key VARCHAR PRIMARY KEY,
            scenario_name VARCHAR NOT NULL,
            pd_multiplier DOUBLE NOT NULL
        )
        """
    )
    connection.executemany(
        "INSERT INTO dim_scenario VALUES (?, ?, ?)",
        [(item.key, item.display_name, item.pd_multiplier) for item in config.scenarios],
    )


def _export_table(
    connection: duckdb.DuckDBPyConnection, table_name: str, destination: Path
) -> None:
    escaped = _sql_literal(destination.resolve())
    connection.execute(
        f"COPY (SELECT * FROM {table_name}) TO '{escaped}' (HEADER, DELIMITER ',')"
    )


def build_warehouse(config: ProjectConfig, *, source_path: Path | None = None) -> dict[str, int]:
    import duckdb

    source = (source_path or config.raw_loans_csv).resolve()
    if not source.exists():
        raise FileNotFoundError(f"Raw loan CSV not found: {source}")

    config.warehouse_path.parent.mkdir(parents=True, exist_ok=True)
    config.powerbi_output_dir.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(config.warehouse_path))
    sql_dir = config.repo_root / "sql"
    replacements = {
        "raw_csv_path": _sql_literal(source),
        "snapshot_date": config.snapshot_date.isoformat(),
        "source_observation_date": config.source_observation_date.isoformat(),
        "default_statuses": _sql_list(config.default_statuses),
        "non_default_statuses": _sql_list(config.non_default_statuses),
        "delinquent_statuses": _sql_list(config.delinquent_statuses),
        "charged_off_statuses": _sql_list(config.charged_off_statuses),
        "open_statuses": _sql_list(config.open_statuses),
        "pd_smoothing_observations": str(config.pd_smoothing_observations),
        "fallback_lgd": str(config.fallback_lgd),
        "lgd_smoothing_exposure": str(config.lgd_smoothing_exposure),
    }

    try:
        for sql_file in [
            sql_dir / "10_build_fact_loan.sql",
            sql_dir / "20_build_analytics.sql",
        ]:
            connection.execute(_render_sql(sql_file, replacements))

        _create_scenario_dimension(connection, config)
        connection.execute(_render_sql(sql_dir / "30_build_expected_loss.sql", replacements))

        exports = {
            "mart_executive_summary": "executive_summary.csv",
            "mart_vintage_performance": "vintage_performance.csv",
            "mart_segment_performance": "segment_performance.csv",
            "mart_credit_economics_summary": "credit_economics_summary.csv",
            "mart_segment_economics": "segment_economics.csv",
            "mart_open_book_summary": "open_book_summary.csv",
            "mart_open_book_segments": "open_book_segments.csv",
            "mart_expected_loss_summary": "expected_loss_summary.csv",
            "mart_expected_loss_scenarios": "expected_loss_scenarios.csv",
            "mart_data_quality_summary": "data_quality_summary.csv",
            "mart_reconciliation_checks": "reconciliation_checks.csv",
        }

        failed_checks = connection.execute(
            "SELECT check_name FROM mart_reconciliation_checks WHERE NOT passed"
        ).fetchall()
        if failed_checks:
            names = ", ".join(row[0] for row in failed_checks)
            raise ValueError(f"Warehouse reconciliation failed: {names}")

        for table_name, filename in exports.items():
            _export_table(connection, table_name, config.powerbi_output_dir / filename)

        row_counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ["fact_loan", *exports]
        }
        return row_counts
    finally:
        connection.close()
