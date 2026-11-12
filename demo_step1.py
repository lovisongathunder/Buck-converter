import sys

sys.path.insert(0, "src")

from buckdesign.calc import design_buck
from buckdesign.specification import BuckSpec

spec = BuckSpec(vin=12, vout=5, iout=2, fsw=500e3)
d = design_buck(spec)

print(f"Duty cycle:          {d.duty:.3f}")
print(f"Ripple current:      {d.delta_il:.2f} A (peak-to-peak)")
print(f"Inductor:            {d.inductance * 1e6:.2f} uH")
print(f"Output capacitor:    {d.capacitance * 1e6:.2f} uF (minimum)")
print(f"Inductor peak/valley:{d.il_peak:.2f} A / {d.il_valley:.2f} A")
print(f"CCM boundary:        {d.i_crit:.2f} A load current")