from dataclasses import dataclass

VCE_SAT = 0.2

REGION_CUTOFF = "cutoff"
REGION_ACTIVE = "active"
REGION_SATURATION = "saturation"

CUTOFF_WARNING = (
    "The transistor is in cutoff: the base loop cannot supply forward current."
)
SATURATION_WARNING = (
    "The transistor is in saturation (VCE ≤ 0.2 V); this operating point is "
    "not valid for amplifier use."
)
NEAR_CUTOFF_WARNING = (
    "Very low base current (IB < 1 µA): the bias is very sensitive to β."
)


@dataclass(frozen=True)
class BiasInputs:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


@dataclass(frozen=True)
class OperatingPoint:
    ib: float
    ic: float
    ie: float
    vce: float
    vb: float
    ve: float
    vc: float
    vbb: float
    rb: float


@dataclass(frozen=True)
class Region:
    name: str
    warning: str | None = None


def base_voltage(inputs: BiasInputs) -> float:
    return inputs.vcc * inputs.r2 / (inputs.r1 + inputs.r2)


def base_resistance(inputs: BiasInputs) -> float:
    return inputs.r1 * inputs.r2 / (inputs.r1 + inputs.r2)


def classify(op: OperatingPoint) -> Region:
    if op.ib <= 0.0:
        return Region(REGION_CUTOFF, CUTOFF_WARNING)
    if op.vce <= VCE_SAT:
        return Region(REGION_SATURATION, SATURATION_WARNING)
    if op.ib < 1e-6:
        return Region(REGION_ACTIVE, NEAR_CUTOFF_WARNING)
    return Region(REGION_ACTIVE, None)


def cutoff_point(inputs: BiasInputs) -> OperatingPoint:
    vbb = base_voltage(inputs)
    rb = base_resistance(inputs)
    return OperatingPoint(
        ib=0.0,
        ic=0.0,
        ie=0.0,
        vce=inputs.vcc,
        vb=vbb,
        ve=0.0,
        vc=inputs.vcc,
        vbb=vbb,
        rb=rb,
    )


def display_point(inputs: BiasInputs, op: OperatingPoint, region: Region) -> OperatingPoint:
    if region.name == REGION_CUTOFF:
        return cutoff_point(inputs)
    return op
