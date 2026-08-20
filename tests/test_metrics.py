import pytest

from credit_portfolio_analytics.metrics import compare_rates, expected_loss, safe_rate


def test_compare_rates_reports_pp_and_relative_change() -> None:
    result = compare_rates(0.15, 0.20)

    assert result.change_percentage_points == pytest.approx(5.0)
    assert result.relative_change == pytest.approx(1 / 3)


def test_expected_loss() -> None:
    assert expected_loss(100_000, 0.10, 0.60) == pytest.approx(6_000)


def test_expected_loss_rejects_invalid_probability() -> None:
    with pytest.raises(ValueError):
        expected_loss(100_000, 1.10, 0.60)


def test_safe_rate_handles_zero_denominator() -> None:
    assert safe_rate(1, 0) is None

