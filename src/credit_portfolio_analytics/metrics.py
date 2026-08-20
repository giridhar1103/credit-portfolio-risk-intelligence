"""Small, testable metric helpers used in reporting."""

from __future__ import annotations

from dataclasses import asdict, dataclass


def safe_rate(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def percentage_point_change(baseline: float, comparison: float) -> float:
    return (comparison - baseline) * 100


def relative_change(baseline: float, comparison: float) -> float | None:
    if baseline == 0:
        return None
    return (comparison - baseline) / baseline


def expected_loss(exposure: float, probability_default: float, loss_given_default: float) -> float:
    if exposure < 0:
        raise ValueError("Exposure cannot be negative.")
    if not 0 <= probability_default <= 1:
        raise ValueError("Probability of default must be between 0 and 1.")
    if not 0 <= loss_given_default <= 1:
        raise ValueError("Loss given default must be between 0 and 1.")
    return exposure * probability_default * loss_given_default


@dataclass(frozen=True)
class RateComparison:
    baseline_rate: float
    comparison_rate: float
    change_percentage_points: float
    relative_change: float | None

    def to_dict(self) -> dict[str, float | None]:
        return asdict(self)


def compare_rates(baseline: float, comparison: float) -> RateComparison:
    return RateComparison(
        baseline_rate=baseline,
        comparison_rate=comparison,
        change_percentage_points=percentage_point_change(baseline, comparison),
        relative_change=relative_change(baseline, comparison),
    )

