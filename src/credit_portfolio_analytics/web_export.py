"""Create a deterministic, aggregate-only JSON bundle for a hosted dashboard."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from .config import ProjectConfig


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date | datetime):
        return value.isoformat()
    return value


def _records(connection: Any, query: str) -> list[dict[str, Any]]:
    cursor = connection.execute(query)
    columns = [item[0] for item in cursor.description]
    return [
        {column: _json_value(value) for column, value in zip(columns, row, strict=True)}
        for row in cursor.fetchall()
    ]


def build_dashboard_bundle(config: ProjectConfig) -> dict[str, Any]:
    """Read governed marts and return the public dashboard data contract."""
    import duckdb

    if not config.warehouse_path.exists():
        raise FileNotFoundError(f"Warehouse not found: {config.warehouse_path}")

    table_queries = {
        "executive_summary": "SELECT * FROM mart_executive_summary",
        "credit_economics": "SELECT * FROM mart_credit_economics_summary",
        "open_book": "SELECT * FROM mart_open_book_summary",
        "vintage_performance": (
            "SELECT * FROM mart_vintage_performance ORDER BY population_scope, issue_year"
        ),
        "segment_performance": (
            "SELECT * FROM mart_segment_performance ORDER BY segment_type, default_rate DESC"
        ),
        "segment_economics": (
            "SELECT * FROM mart_segment_economics ORDER BY segment_type, default_rate DESC"
        ),
        "open_book_segments": (
            "SELECT * FROM mart_open_book_segments "
            "ORDER BY segment_type, outstanding_exposure DESC"
        ),
        "expected_loss_summary": (
            "SELECT * FROM mart_expected_loss_summary ORDER BY pd_multiplier"
        ),
        "expected_loss_detail": (
            "SELECT * FROM mart_expected_loss_scenarios "
            "ORDER BY pd_multiplier, issue_year, grade, loan_status"
        ),
        "data_quality": "SELECT * FROM mart_data_quality_summary ORDER BY metric",
        "reconciliation_checks": "SELECT * FROM mart_reconciliation_checks ORDER BY check_name",
    }

    connection = duckdb.connect(str(config.warehouse_path), read_only=True)
    try:
        tables = {
            name: _records(connection, query) for name, query in table_queries.items()
        }
    finally:
        connection.close()

    checks_passed = all(row["passed"] for row in tables["reconciliation_checks"])
    if not checks_passed:
        raise ValueError("Dashboard export blocked by failed warehouse reconciliation")

    return {
        "schema_version": "1.0.0",
        "project": "credit-portfolio-risk-analytics",
        "population_contract": {
            "historical_maturity_cutoff": config.snapshot_date.isoformat(),
            "source_observation_month_proxy": config.source_observation_date.isoformat(),
            "historical_exposure": "funded_principal",
            "open_book_ead": "outstanding_principal",
            "scenario_interpretation": "lifetime_benchmark_sensitivity",
        },
        "quality": {
            "warehouse_reconciled": checks_passed,
            "reconciliation_check_count": len(tables["reconciliation_checks"]),
        },
        "tables": tables,
    }


def write_dashboard_bundle(config: ProjectConfig, output_path: Path | None = None) -> Path:
    """Write the hosted-dashboard bundle and return its resolved path."""
    default_path = config.repo_root / "data" / "web" / "credit-risk-dashboard.json"
    destination = (output_path or default_path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        build_dashboard_bundle(config), indent=2, sort_keys=True, allow_nan=False
    )
    destination.write_text(
        serialized + "\n",
        encoding="utf-8",
    )
    return destination
