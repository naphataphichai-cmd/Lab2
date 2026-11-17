import math
from collections.abc import Mapping
from dataclasses import dataclass

from . import model

MODE_FIELDS = {
    model.MODE_DIVIDER: ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
    model.MODE_FIXED: ("vcc", "rb", "rc", "beta", "vbe"),
    model.MODE_EMITTER: ("vcc", "rb", "re", "rc", "beta", "vbe"),
}

REQUIRED_FIELDS = MODE_FIELDS[model.MODE_DIVIDER]
RESISTOR_FIELDS = ("rb", "r1", "r2", "rc", "re")

R_MIN = 1e-3
R_MAX = 10e6

MODE_ERROR = "Choose a supported circuit mode."


@dataclass(frozen=True)
class FieldError:
    field: str
    message: str


def parse_mode(raw: str | None) -> tuple[str | None, FieldError | None]:
    text = raw.strip() if isinstance(raw, str) else ""
    if not text:
        return model.MODE_DIVIDER, None
    if text in MODE_FIELDS:
        return text, None
    return None, FieldError("mode", MODE_ERROR)


def parse_inputs_for_mode(
    form: Mapping[str, str],
    mode: str,
) -> tuple[
    model.BiasInputs | model.FixedBiasInputs | model.EmitterBiasInputs | None,
    list[FieldError],
]:
    fields = MODE_FIELDS.get(mode)
    if fields is None:
        return None, [FieldError("mode", MODE_ERROR)]

    errors: list[FieldError] = []
    values: dict[str, float] = {}

    for field in fields:
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

    if mode == model.MODE_FIXED:
        return model.FixedBiasInputs(**values), []
    if mode == model.MODE_EMITTER:
        return model.EmitterBiasInputs(**values), []
    return model.BiasInputs(**values), []


def parse_inputs(
    form: Mapping[str, str],
) -> tuple[model.BiasInputs | None, list[FieldError]]:
    inputs, errors = parse_inputs_for_mode(form, model.MODE_DIVIDER)
    return inputs, errors
