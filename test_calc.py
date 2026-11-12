"""Check the formulas against hand-worked numbers.

Reference case: 12 V -> 5 V, 2 A, 500 kHz, 30 % ripple current, 50 mV ripple.
  D        = 5 / 12                       = 0.41667
  delta_IL = 0.3 * 2                      = 0.6 A
  L        = 5 * 7 / (12 * 500e3 * 0.6)   = 9.722 uH
  C        = 0.6 / (8 * 500e3 * 0.05)     = 3 uF
  peak     = 2 + 0.3                      = 2.3 A
  valley   = 2 - 0.3                      = 1.7 A
  I_crit   = 0.6 / 2                      = 0.3 A
"""

import pytest

from buckdesign.calc import (
    design_buck,
    duty_cycle,
    inductance,
    output_capacitance,
)
from buckdesign.specification import BuckSpec


@pytest.fixture
def spec():
    return BuckSpec(vin=12, vout=5, iout=2, fsw=500e3)


def test_duty_cycle():
    assert duty_cycle(12, 5) == pytest.approx(0.41667, rel=1e-4)


def test_inductance():
    assert inductance(12, 5, 500e3, 0.6) == pytest.approx(9.722e-6, rel=1e-3)


def test_output_capacitance():
    assert output_capacitance(0.6, 500e3, 0.05) == pytest.approx(3e-6, rel=1e-6)


def test_full_design(spec):
    result = design_buck(spec)
    assert result.duty == pytest.approx(0.41667, rel=1e-4)
    assert result.delta_il == pytest.approx(0.6)
    assert result.inductance == pytest.approx(9.722e-6, rel=1e-3)
    assert result.capacitance == pytest.approx(3e-6, rel=1e-6)
    assert result.il_peak == pytest.approx(2.3)
    assert result.il_valley == pytest.approx(1.7)
    assert result.i_crit == pytest.approx(0.3)


def test_higher_frequency_needs_smaller_parts(spec):
    fast = BuckSpec(vin=12, vout=5, iout=2, fsw=1e6)
    assert design_buck(fast).inductance < design_buck(spec).inductance
    assert design_buck(fast).capacitance < design_buck(spec).capacitance


def test_vout_must_be_below_vin():
    with pytest.raises(ValueError):
        BuckSpec(vin=5, vout=12, iout=2, fsw=500e3)


def test_rejects_non_positive_values():
    with pytest.raises(ValueError):
        BuckSpec(vin=12, vout=5, iout=0, fsw=500e3)


def test_rejects_bad_ripple_ratio():
    with pytest.raises(ValueError):
        BuckSpec(vin=12, vout=5, iout=2, fsw=500e3, ripple_current_ratio=1.5)