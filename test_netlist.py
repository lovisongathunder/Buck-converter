import pytest

from buckdesign.calc import design_buck
from buckdesign.netlist import render_netlist, write_netlist
from buckdesign.specification import BuckSpec


@pytest.fixture
def netlist():
    spec = BuckSpec(vin=12, vout=5, iout=2, fsw=500e3)
    return render_netlist(spec, design_buck(spec))


def test_contains_all_power_components(netlist):
    for part in ("Vin vin 0 12", "S1 vin sw gate 0 SW", "D1 0 sw DIDEAL",
                 "L1 sw vout", "C1 vout 0", "Rload vout 0 2.5"):
        assert part in netlist


def test_gate_pulse_matches_duty_cycle(netlist):
    assert "PULSE(0 5 0 1n 1n 8.33333e-07 2e-06)" in netlist


def test_inductor_value_comes_from_calc(netlist):
    assert "L1 sw vout 9.72222e-06" in netlist


def test_simulation_and_measurements_present(netlist):
    assert ".tran 0 0.0008 0 1e-08" in netlist
    for name in ("vout_avg", "vout_pp", "il_max", "il_min", "pin", "pout", "eff"):
        assert name in netlist
    assert netlist.strip().endswith(".end")


def test_no_unfilled_template_markers(netlist):
    assert "{{" not in netlist and "}}" not in netlist


def test_write_netlist_creates_folder(tmp_path, netlist):
    out = write_netlist(netlist, tmp_path / "sims" / "buck.cir")
    assert out.read_text() == netlist