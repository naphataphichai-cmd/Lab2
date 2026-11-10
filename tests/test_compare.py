from engineering import compare, model


def _op(**overrides):
    values = dict(
        ib=8.824501487275532e-06,
        ic=0.0013236752230913297,
        ie=0.0013324997245786052,
        vce=4.446226726892145,
        vb=2.0324997245786052,
        ve=1.3324997245786052,
        vc=5.77872645147075,
        vbb=2.1052631578947367,
        rb=8245.614035087719,
    )
    values.update(overrides)
    return model.OperatingPoint(**values)


def test_identical_points_match():
    result = compare.compare(_op(), _op())
    assert result.match is True
    assert result.max_rel_error == 0.0
    assert result.mismatches == ()


def test_tiny_relative_difference_matches():
    result = compare.compare(_op(), _op(ic=0.0013236752230913297 * (1.0 + 1e-7)))
    assert result.match is True


def test_large_difference_is_a_mismatch():
    result = compare.compare(_op(), _op(ic=0.002))
    assert result.match is False
    assert "ic" in result.mismatches
    assert result.max_rel_error > 1e-6


def test_zero_valued_cutoff_points_match():
    zero = _op(ib=0.0, ic=0.0, ie=0.0)
    assert compare.compare(zero, zero).match is True


def test_zero_versus_nonzero_is_a_mismatch():
    result = compare.compare(_op(ib=0.0), _op())
    assert result.match is False
    assert "ib" in result.mismatches


def test_combine_reports_region_mismatch():
    same = compare.compare(_op(), _op())
    result = compare.combine(same, same, region_a="active", region_b="cutoff")
    assert result.match is False
    assert "region" in result.mismatches


def test_combine_unions_numeric_mismatches():
    good = compare.compare(_op(), _op())
    bad = compare.compare(_op(), _op(ic=0.002))
    result = compare.combine(good, bad, region_a="active", region_b="active")
    assert result.match is False
    assert "ic" in result.mismatches
