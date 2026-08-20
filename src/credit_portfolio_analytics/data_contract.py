"""Raw LendingClub CSV contract and provenance validation."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = frozenset(
    {
        "id",
        "loan_amnt",
        "funded_amnt",
        "out_prncp",
        "term",
        "int_rate",
        "grade",
        "sub_grade",
        "annual_inc",
        "issue_d",
        "loan_status",
        "purpose",
        "dti",
        "addr_state",
        "earliest_cr_line",
        "total_pymnt",
        "total_rec_prncp",
        "total_rec_int",
        "total_rec_late_fee",
        "recoveries",
        "collection_recovery_fee",
        "last_pymnt_d",
        "last_credit_pull_d",
    }
)


@dataclass(frozen=True)
class DataValidationResult:
    path: str
    exists: bool
    valid: bool
    file_size_bytes: int | None
    column_count: int | None
    required_column_count: int
    missing_columns: tuple[str, ...]
    row_count: int | None = None
    sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def _read_header(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return tuple(column.strip() for column in next(reader))
        except StopIteration as exc:
            raise ValueError(f"Source file is empty: {path}") from exc


def _deep_profile(path: Path) -> tuple[int, str]:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = sum(1 for row in csv.reader(handle) if any(cell.strip() for cell in row))

    return max(rows - 1, 0), digest.hexdigest()


def validate_csv(path: Path | str, *, deep: bool = False) -> DataValidationResult:
    source = Path(path).resolve()
    if not source.exists():
        return DataValidationResult(
            path=str(source),
            exists=False,
            valid=False,
            file_size_bytes=None,
            column_count=None,
            required_column_count=len(REQUIRED_COLUMNS),
            missing_columns=tuple(sorted(REQUIRED_COLUMNS)),
        )

    header = _read_header(source)
    missing = tuple(sorted(REQUIRED_COLUMNS.difference(header)))
    row_count = None
    checksum = None
    if deep:
        row_count, checksum = _deep_profile(source)

    return DataValidationResult(
        path=str(source),
        exists=True,
        valid=not missing,
        file_size_bytes=source.stat().st_size,
        column_count=len(header),
        required_column_count=len(REQUIRED_COLUMNS),
        missing_columns=missing,
        row_count=row_count,
        sha256=checksum,
    )
