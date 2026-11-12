import sys

sys.path.insert(0, "src")

from buckdesign.calc import design_buck
from buckdesign.netlist import render_netlist, write_netlist
from buckdesign.specification import BuckSpec

spec = BuckSpec(vin=12, vout=5, iout=2, fsw=500e3)
design = design_buck(spec)

netlist = render_netlist(spec, design)
path = write_netlist(netlist, "sims/buck_12v_5v_2a.cir")
print(f"Wrote {path}")