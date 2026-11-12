"""Confirm the 3.9 uF choice (x1.3) with fresh random draws."""

import sys
from dataclasses import replace

sys.path.insert(0, "src")

from buckdesign.calc import design_buck
from buckdesign.report import plot_results, save_csv
from buckdesign.specification import BuckSpec
from buckdesign.tolerance import PassCriteria, Tolerances, run_monte_carlo, summarize

spec = BuckSpec(vin=12, vout=5, iout=2, fsw=500e3)
design = design_buck(spec)
criteria = PassCriteria(vout_min=4.85, vout_max=5.15, vout_pp_max=0.060, il_peak_max=2.5)

sized = replace(design, capacitance=design.capacitance * 1.3)
records = run_monte_carlo(spec, sized, Tolerances(), criteria, n=300, seed=3,
                          folder="sims/confirm_39uf", progress=False)
print(summarize(records))
save_csv(records, "reports/confirm_39uF.csv")
plot_results(records, criteria, "reports/confirm_39uF.png")