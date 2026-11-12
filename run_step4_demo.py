"""Tolerance analysis: how often does the design still meet spec?"""

import sys

sys.path.insert(0, "src")

from buckdesign.calc import design_buck
from buckdesign.report import plot_results, save_csv
from buckdesign.specification import BuckSpec
from buckdesign.tolerance import PassCriteria, Tolerances, run_monte_carlo, summarize

spec = BuckSpec(vin=12, vout=5, iout=2, fsw=500e3)
design = design_buck(spec)

tolerances = Tolerances()  # L +/-20 %, C +/-20 %, ESR +/-50 %, DCR +/-20 %, Ron +/-30 %
criteria = PassCriteria(
    vout_min=4.85,      # within 3 % of 5 V
    vout_max=5.15,
    vout_pp_max=0.060,  # 60 mV ripple limit (20 % above the 50 mV design target)
    il_peak_max=2.5,    # inductor saturation rating
)

records = run_monte_carlo(spec, design, tolerances, criteria, n=100, seed=1)

print()
print(summarize(records))
print("Saved:", save_csv(records, "reports/montecarlo_12v_5v_2a.csv"))
print("Saved:", plot_results(records, criteria, "reports/montecarlo_12v_5v_2a.png"))