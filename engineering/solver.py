from . import model


def solve(inputs: model.BiasInputs) -> model.OperatingPoint:
    vbb = model.base_voltage(inputs)
    rb = model.base_resistance(inputs)

    ib = (vbb - inputs.vbe) / (rb + (inputs.beta + 1.0) * inputs.re)
    ic = inputs.beta * ib
    ie = (inputs.beta + 1.0) * ib
    ve = ie * inputs.re
    vc = inputs.vcc - ic * inputs.rc
    vb = ve + inputs.vbe
    vce = vc - ve

    return model.OperatingPoint(
        ib=ib,
        ic=ic,
        ie=ie,
        vce=vce,
        vb=vb,
        ve=ve,
        vc=vc,
        vbb=vbb,
        rb=rb,
    )


def solve_fixed(inputs: model.FixedBiasInputs) -> model.OperatingPoint:
    ib = (inputs.vcc - inputs.vbe) / inputs.rb
    ic = inputs.beta * ib
    ie = (inputs.beta + 1.0) * ib
    ve = 0.0
    vc = inputs.vcc - ic * inputs.rc
    vb = inputs.vbe
    vce = vc - ve

    return model.OperatingPoint(
        ib=ib,
        ic=ic,
        ie=ie,
        vce=vce,
        vb=vb,
        ve=ve,
        vc=vc,
        vbb=0.0,
        rb=inputs.rb,
    )


def solve_emitter(inputs: model.EmitterBiasInputs) -> model.OperatingPoint:
    ib = (inputs.vcc - inputs.vbe) / (
        inputs.rb + (inputs.beta + 1.0) * inputs.re
    )
    ic = inputs.beta * ib
    ie = (inputs.beta + 1.0) * ib
    ve = ie * inputs.re
    vc = inputs.vcc - ic * inputs.rc
    vb = ve + inputs.vbe
    vce = vc - ve

    return model.OperatingPoint(
        ib=ib,
        ic=ic,
        ie=ie,
        vce=vce,
        vb=vb,
        ve=ve,
        vc=vc,
        vbb=0.0,
        rb=inputs.rb,
    )
