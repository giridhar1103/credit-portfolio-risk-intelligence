from pathlib import Path

from credit_portfolio_analytics.data_contract import REQUIRED_COLUMNS, validate_csv

FIXTURE = Path(__file__).parent / "fixtures" / "loans_sample.csv"


def test_sample_csv_satisfies_contract() -> None:
    result = validate_csv(FIXTURE, deep=True)

    assert result.valid
    assert result.row_count == 6
    assert result.column_count == len(REQUIRED_COLUMNS)
    assert result.sha256 is not None


def test_missing_file_fails_contract(tmp_path: Path) -> None:
    result = validate_csv(tmp_path / "missing.csv")

    assert not result.exists
    assert not result.valid
    assert set(result.missing_columns) == REQUIRED_COLUMNS

