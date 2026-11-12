"""Find the smallest output capacitance that gives 99 % yield, then confirm it."""

import sys
from dataclasses import replace

sys.path.insert(0, "src")

from buckdesign.calc import design_buck
from buckdesign.report import plot_results, save_csv
from buckdesign.specification import BuckSpec
from buckdesign.sweep import smallest_passing, sweep_capacitance
from buckdesign.tolerance import PassCriteria, Tolerances, run_monte_carlo, summarize

spec = BuckSpec(vin=12, vout=5, iout=2, fsw=500e3)
design = design_buck(spec)
tolerances = Tolerances()
criteria = PassCriteria(vout_min=4.85, vout_max=5.15, vout_pp_max=0.060, il_peak_max=2.5)

points = sweep_capacitance(spec, design, tolerances, criteria,
                           scales=[1.0, 1.1, 1.2, 1.3, 1.4], n=100)

best = smallest_passing(points, target=0.99)
if best is None:
    sys.exit("No tested capacitance reached 99 % yield. Extend the scales and retry.")
print(f"\nSmallest passing value: {best.capacitance * 1e6:.2f} uF (x{best.scale:.2f})")

# Fresh random draws (new seed) so the check is independent of the sweep.
sized = replace(design, capacitance=best.capacitance)
confirm = run_monte_carlo(spec, sized, tolerances, criteria, n=300, seed=2,
                          folder="sims/confirm", progress=False)
print()
print(summarize(confirm))
save_csv(confirm, "reports/confirm_montecarlo.csv")
plot_results(confirm, criteria, "reports/confirm_montecarlo.png")