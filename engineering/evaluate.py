from dataclasses import dataclass

from . import compare, crosscheck, model, solver


@dataclass(frozen=True)
class Evaluation:
    inputs: model.BiasInputs
    analytical_raw: model.OperatingPoint
    independent_raw: model.OperatingPoint
    analytical: model.OperatingPoint
    independent: model.OperatingPoint
    region: model.Region
    comparison: compare.Comparison


def evaluate(inputs: model.BiasInputs) -> Evaluation:
    analytical_raw = solver.solve(inputs)
    independent_raw = crosscheck.solve(inputs)

    analytical_region = model.classify(analytical_raw)
    independent_region = model.classify(independent_raw)

    analytical = model.display_point(inputs, analytical_raw, analytical_region)
    independent = model.display_point(inputs, independent_raw, independent_region)

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
    )
