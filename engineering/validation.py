import math
from collections.abc import Mapping
from dataclasses import dataclass

from . import model

REQUIRED_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
RESISTOR_FIELDS = ("r1", "r2", "rc", "re")

R_MIN = 1e-3
R_MAX = 10e6


@dataclass(frozen=True)
class FieldError:
    field: str
    message: str


def parse_inputs(
    form: Mapping[str, str],
) -> tuple[model.BiasInputs | None, list[FieldError]]:
    errors: list[FieldError] = []
    values: dict[str, float] = {}

    for field in REQUIRED_FIELDS:
        raw = form.get(field, "")
        text = raw.strip() if isinstance(raw, str) else str(raw).strip()

        if not text:
            errors.append(FieldError(field, "Required."))
            continue

        try:
            value = float(text)
        except ValueError:
            errors.append(FieldError(field, "Must be a number."))
            continue

        if not math.isfinite(value):
            errors.append(FieldError(field, "Must be a finite number."))
            continue

        values[field] = value

    if "vcc" in values and not (0.0 < values["vcc"] <= 100.0):
        errors.append(
            FieldError("vcc", "Must be greater than 0 and at most 100 V.")
        )

    for field in RESISTOR_FIELDS:
        if field in values and not (R_MIN <= values[field] <= R_MAX):
            errors.append(
                FieldError(field, "Must be between 1 mΩ and 10 MΩ.")
            )

    if "beta" in values and not (1.0 < values["beta"] <= 2000.0):
        errors.append(
            FieldError("beta", "Must be greater than 1 and at most 2000.")
        )

    if "vbe" in values:
        if values["vbe"] < 0.0:
            errors.append(FieldError("vbe", "Must be 0 V or more."))
        elif "vcc" in values and values["vbe"] >= values["vcc"]:
            errors.append(FieldError("vbe", "Must be less than VCC."))

    if errors:
        return None, errors

    return model.BiasInputs(**values), []
