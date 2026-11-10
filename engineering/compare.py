import math
from dataclasses import dataclass

from . import model

FIELDS = ("ib", "ic", "ie", "vce", "vb", "ve", "vc")


@dataclass(frozen=True)
class Comparison:
    match: bool
    max_rel_error: float
    mismatches: tuple[str, ...]


def _relative_error(a: float, b: float) -> float:
    denominator = max(abs(a), abs(b))
    if denominator == 0.0:
        return 0.0
    return abs(a - b) / denominator


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(1e-12, 1e-6 * max(abs(a), abs(b)))


def compare(a: model.OperatingPoint, b: model.OperatingPoint) -> Comparison:
    mismatches = []
    max_rel_error = 0.0

    for field in FIELDS:
        left = getattr(a, field)
        right = getattr(b, field)

        if not math.isfinite(left) or not math.isfinite(right):
            mismatches.append(field)
            max_rel_error = math.inf
            continue

        max_rel_error = max(max_rel_error, _relative_error(left, right))
        if not _close(left, right):
            mismatches.append(field)

    return Comparison(not mismatches, max_rel_error, tuple(mismatches))


def combine(
    *comparisons: Comparison,
    region_a: str,
    region_b: str,
) -> Comparison:
    mismatches = []
    max_rel_error = 0.0

    for comparison in comparisons:
        max_rel_error = max(max_rel_error, comparison.max_rel_error)
        for field in comparison.mismatches:
            if field not in mismatches:
                mismatches.append(field)

    if region_a != region_b:
        mismatches.append("region")

    return Comparison(not mismatches, max_rel_error, tuple(mismatches))
