from dataclasses import dataclass

from . import compare, crosscheck, model, solver

Inputs = model.BiasInputs | model.FixedBiasInputs | model.EmitterBiasInputs


@dataclass(frozen=True)
class Evaluation:
    inputs: Inputs
    analytical_raw: model.OperatingPoint
    independent_raw: model.OperatingPoint
    analytical: model.OperatingPoint
    independent: model.OperatingPoint
    region: model.Region
    comparison: compare.Comparison
    mode: str = model.MODE_DIVIDER


def _paths(mode: str):
    if mode == model.MODE_DIVIDER:
        return solver.solve, crosscheck.solve
    if mode == model.MODE_FIXED:
        return solver.solve_fixed, crosscheck.solve_fixed
    if mode == model.MODE_EMITTER:
        return solver.solve_emitter, crosscheck.solve_emitter
    raise ValueError(f"unknown bias mode: {mode}")


def evaluate(inputs: Inputs, mode: str = model.MODE_DIVIDER) -> Evaluation:
    analytical_solve, independent_solve = _paths(mode)

    analytical_raw = analytical_solve(inputs)
    independent_raw = independent_solve(inputs)

    analytical_region = model.classify(analytical_raw)
    independent_region = model.classify(independent_raw)

    analytical = model.display_point(inputs, analytical_raw, analytical_region, mode)
    independent = model.display_point(inputs, independent_raw, independent_region, mode)

    raw_comparison = compare.compare(analytical_raw, independent_raw)
    display_comparison = compare.compare(analytical, independent)
    comparison = compare.combine(
        raw_comparison,
        display_comparison,
        region_a=analytical_region.name,
        region_b=independent_region.name,
    )

    return Evaluation(
        inputs=inputs,
        analytical_raw=analytical_raw,
        independent_raw=independent_raw,
        analytical=analytical,
        independent=independent,
        region=analytical_region,
        comparison=comparison,
        mode=mode,
    )
