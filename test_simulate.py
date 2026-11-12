import pytest

from buckdesign.calc import design_buck
from buckdesign.compare import compare, format_comparison
from buckdesign.simulate import parse_measurements, result_from_log
from buckdesign.specification import BuckSpec

# Taken from a real LTspice run of the reference design.
SAMPLE_LOG = """\
LTspice 26.1.1 for Windows
Circuit: D:\\Power supply design assistant\\sims\\buck_12v_5v_2a.cir
solver = Normal
tnom = 27
Direct Newton iteration succeeded in finding operating point.
Total elapsed time: 0.873 seconds.

vout_avg: AVG(V(vout))=4.94708488409 FROM 0.00076 TO 0.0008
vout_pp: PP(V(vout))=0.0502324104309 FROM 0.00076 TO 0.0008
il_max: MAX(I(L1))=2.2797665596 FROM 0.00076 TO 0.0008
il_min: MIN(I(L1))=1.67807173729 FROM 0.00076 TO 0.0008
pin: AVG(-V(vin)*I(Vin))=9.9081317815 FROM 0.00076 TO 0.0008
pout: AVG(V(vout)*I(Rload))=9.78959217631 FROM 0.00076 TO 0.0008
eff: pout/pin=0.988036129534
"""


def test_parse_measurements_reads_all_values():
    values = parse_measurements(SAMPLE_LOG)
    assert values["vout_avg"] == pytest.approx(4.94708488409)
    assert values["pin"] == pytest.approx(9.9081317815)
    assert values["eff"] == pytest.approx(0.988036129534)
    assert len(values) == 7


def test_parse_measurements_handles_windows_line_endings():
    values = parse_measurements(SAMPLE_LOG.replace("\n", "\r\n"))
    assert values["eff"] == pytest.approx(0.988036129534)


def test_parse_measurements_handles_scientific_notation():
    values = parse_measurements("x: AVG(V(a))=1.5e-03 FROM 0 TO 1\n")
    assert values["x"] == pytest.approx(1.5e-3)


def test_result_from_log_computes_inductor_ripple():
    result = result_from_log(SAMPLE_LOG)
    assert result.il_pp == pytest.approx(0.6017, abs=1e-3)


def test_missing_measurement_gives_clear_error():
    with pytest.raises(ValueError, match="missing"):
        result_from_log("vout_avg: AVG(V(vout))=5 FROM 0 TO 1\n")


def test_compare_matches_hand_checked_numbers():
    spec = BuckSpec(vin=12, vout=5, iout=2, fsw=500e3)
    design = design_buck(spec)
    result = result_from_log(SAMPLE_LOG)
    rows = {r.name: r for r in compare(spec, design, result)}
    assert rows["Average output voltage"].error_pct == pytest.approx(-1.06, abs=0.01)
    assert rows["Inductor ripple current (pp)"].error_pct == pytest.approx(0.28, abs=0.05)
    text = format_comparison(list(rows.values()), result)
    assert "98.8 %" in text