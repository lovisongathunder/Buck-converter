import pytest

from buckdesign import tolerance
from buckdesign.calc import design_buck
from buckdesign.report import save_csv
from buckdesign.simulate import SimResult
from buckdesign.specification import BuckSpec
from buckdesign.tolerance import (
    PassCriteria,
    Tolerances,
    draw_samples,
    run_monte_carlo,
    summarize,
)

SPEC = BuckSpec(vin=12, vout=5, iout=2, fsw=500e3)
DESIGN = design_buck(SPEC)
CRITERIA = PassCriteria(vout_min=4.85, vout_max=5.15, vout_pp_max=0.060, il_peak_max=2.5)

FAKE_LOG = """\
vout_avg: AVG(V(vout))=4.95 FROM 0 TO 1
vout_pp: PP(V(vout))=0.07 FROM 0 TO 1
il_max: MAX(I(L1))=2.3 FROM 0 TO 1
il_min: MIN(I(L1))=1.7 FROM 0 TO 1
pin: AVG(-V(vin)*I(Vin))=9.9 FROM 0 TO 1
pout: AVG(V(vout)*I(Rload))=9.8 FROM 0 TO 1
eff: pout/pin=0.99
"""


def make_fake_run(tmp_path):
    """Stand-in for run_netlist that writes a canned log instead of running LTspice."""

    def fake_run(cir_path, output_folder):
        log = tmp_path / (cir_path.stem + ".log")
        log.write_text(FAKE_LOG)
        return log

    return fake_run


def make_result(**changes):
    values = dict(vout_avg=4.95, vout_pp=0.05, il_max=2.3, il_min=1.7,
                  pin=9.9, pout=9.8, eff=0.99)
    values.update(changes)
    return SimResult(**values)


def test_samples_stay_inside_tolerance_bands():
    tol = Tolerances()
    for s in draw_samples(DESIGN, tol, n=200, seed=3):
        assert abs(s.inductance / DESIGN.inductance - 1) <= tol.inductance + 1e-9
        assert abs(s.capacitance / DESIGN.capacitance - 1) <= tol.capacitance + 1e-9


def test_same_seed_gives_same_samples():
    a = draw_samples(DESIGN, Tolerances(), n=10, seed=7)
    b = draw_samples(DESIGN, Tolerances(), n=10, seed=7)
    assert a == b


def test_different_seed_gives_different_samples():
    a = draw_samples(DESIGN, Tolerances(), n=10, seed=7)
    b = draw_samples(DESIGN, Tolerances(), n=10, seed=8)
    assert a != b


def test_good_result_passes():
    assert CRITERIA.failures(make_result()) == []


def test_each_limit_is_checked():
    assert "Output ripple too high" in CRITERIA.failures(make_result(vout_pp=0.07))
    assert "Output voltage outside window" in CRITERIA.failures(make_result(vout_avg=4.7))
    assert "Inductor peak current too high" in CRITERIA.failures(make_result(il_max=2.6))


def test_monte_carlo_loop_with_fake_simulator(tmp_path, monkeypatch):
    monkeypatch.setattr(tolerance, "run_netlist", make_fake_run(tmp_path))
    records = run_monte_carlo(SPEC, DESIGN, Tolerances(), CRITERIA, n=5,
                              folder=tmp_path / "mc", progress=False)
    assert len(records) == 5
    assert all(r.failures == ["Output ripple too high"] for r in records)
    assert "Passed: 0 (0 %)" in summarize(records)


def test_csv_has_header_and_one_row_per_run(tmp_path, monkeypatch):
    monkeypatch.setattr(tolerance, "run_netlist", make_fake_run(tmp_path))
    records = run_monte_carlo(SPEC, DESIGN, Tolerances(), CRITERIA, n=3,
                              folder=tmp_path / "mc", progress=False)
    out = save_csv(records, tmp_path / "r.csv")
    assert len(out.read_text().strip().splitlines()) == 4