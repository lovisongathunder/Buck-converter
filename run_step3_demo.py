"""Run the reference design through LTspice and compare with the calculations."""

import sys

sys.path.insert(0, "src")

from buckdesign.calc import design_buck
from buckdesign.compare import compare, format_comparison
from buckdesign.simulate import simulate_design
from buckdesign.specification import BuckSpec

spec = BuckSpec(vin=12, vout=5, iout=2, fsw=500e3)
design = design_buck(spec)

result = simulate_design(spec, design, name="buck_12v_5v_2a")
print(format_comparison(compare(spec, design, result), result))