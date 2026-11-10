import math


def _require_finite(value: float) -> None:
    if not math.isfinite(value):
        raise ValueError("non-finite value")


def format_current(amps: float) -> tuple[str, str]:
    _require_finite(amps)
    magnitude = abs(amps)
    if magnitude < 1e-3:
        return f"{amps * 1e6:.4g}", "µA"
    if magnitude < 1.0:
        return f"{amps * 1e3:.4g}", "mA"
    return f"{amps:.4g}", "A"


def format_voltage(volts: float) -> tuple[str, str]:
    _require_finite(volts)
    return f"{volts:.4g}", "V"


def format_resistance(ohms: float) -> tuple[str, str]:
    _require_finite(ohms)
    magnitude = abs(ohms)
    if magnitude >= 1e6:
        return f"{ohms / 1e6:.4g}", "MΩ"
    if magnitude >= 1e3:
        return f"{ohms / 1e3:.4g}", "kΩ"
    return f"{ohms:.4g}", "Ω"


def format_error(value: float) -> str:
    if not math.isfinite(value):
        return "inf"
    return f"{value:.1e}"
