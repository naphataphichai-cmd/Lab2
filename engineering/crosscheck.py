from . import model


def gaussian_solve(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    n = len(rhs)
    if len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be square")

    a = [list(row) + [rhs[i]] for i, row in enumerate(matrix)]

    for col in range(n):
        pivot_row = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot_row][col]) < 1e-15:
            raise ValueError("singular system")
        if pivot_row != col:
            a[col], a[pivot_row] = a[pivot_row], a[col]

        pivot = a[col][col]
        for j in range(col, n + 1):
            a[col][j] /= pivot

        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            if factor == 0.0:
                continue
            for j in range(col, n + 1):
                a[row][j] -= factor * a[col][j]

    return [a[i][n] for i in range(n)]


def solve(inputs: model.BiasInputs) -> model.OperatingPoint:
    vbb = model.base_voltage(inputs)
    rb = model.base_resistance(inputs)

    g1 = 1.0 / inputs.r1
    g2 = 1.0 / inputs.r2
    gc = 1.0 / inputs.rc
    ge = 1.0 / inputs.re
    b1 = inputs.beta + 1.0

    matrix = [
        [-(g1 + g2), -ge / b1, 0.0],
        [0.0, -inputs.beta * ge / b1, -gc],
        [1.0, -1.0, 0.0],
    ]
    rhs = [-inputs.vcc / inputs.r1, -inputs.vcc / inputs.rc, inputs.vbe]

    vb, ve, vc = gaussian_solve(matrix, rhs)

    ib = ve / (b1 * inputs.re)
    ic = inputs.beta * ib
    ie = ve / inputs.re
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
