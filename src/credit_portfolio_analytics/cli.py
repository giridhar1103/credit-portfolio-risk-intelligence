"""Command-line interface for validation and warehouse builds."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ProjectConfig, default_config_path
from .data_contract import validate_csv
from .database import build_warehouse
from .reporting import write_executive_report
from .web_export import write_dashboard_bundle


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Credit portfolio risk analytics pipeline")
    parser.add_argument(
        "--config",
        type=Path,
        default=default_config_path(),
        help="Path to the project TOML configuration",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-data", help="Validate the raw LendingClub CSV")
    validate.add_argument("--input", type=Path, help="Optional source CSV override")
    validate.add_argument(
        "--deep",
        action="store_true",
        help="Calculate full row count and SHA-256 checksum",
    )

    build = commands.add_parser("build", help="Build DuckDB marts and Power BI exports")
    build.add_argument("--input", type=Path, help="Optional source CSV override")

    report = commands.add_parser("report", help="Generate the executive credit-risk review")
    report.add_argument("--output", type=Path, help="Optional Markdown output path")
    report.add_argument(
        "--minimum-segment-loans",
        type=int,
        default=1_000,
        help="Minimum loans required for high/low segment comparisons",
    )

    web_export = commands.add_parser(
        "export-web", help="Export the reconciled aggregate dashboard JSON bundle"
    )
    web_export.add_argument("--output", type=Path, help="Optional JSON output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = ProjectConfig.load(args.config)

    if args.command == "validate-data":
        source = (args.input or config.raw_loans_csv).resolve()
        result = validate_csv(source, deep=args.deep)
        print(result.to_json())
        return 0 if result.valid else 1

    if args.command == "report":
        output = write_executive_report(
            config,
            args.output,
            minimum_segment_loans=args.minimum_segment_loans,
        )
        print(f"Executive review written to {output}")
        return 0

    if args.command == "export-web":
        output = write_dashboard_bundle(config, args.output)
        print(f"Dashboard bundle written to {output}")
        return 0

    source = (args.input or config.raw_loans_csv).resolve()
    validation = validate_csv(source)
    if not validation.valid:
        print(validation.to_json(), file=sys.stderr)
        return 1

    counts = build_warehouse(config, source_path=source)
    print("Warehouse build completed.")
    for table, count in counts.items():
        print(f"  {table}: {count:,} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
