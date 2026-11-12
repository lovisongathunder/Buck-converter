# Buck Converter Design Assistant

A Python tool that designs a DC-DC buck converter from a specification, simulates it in LTspice, and tests how well the design survives real-world component tolerances. Everything runs in software: no hardware is required.

## Why I built this

I’m interested in semiconductors because I want to understand how chips actually work. Every chip depends on stable power, so I started with exploring power delivery. I built a tool that automates the repetitive math of designing a buck converter, then simulates how the design behaves with real, imperfect components. My goal was to close the gap between textbook formulas and real-world behavior, and the tolerance analysis showed me that a design that looks perfect on paper can fail in 15% of builds.


## Problem

Designing a power supply usually means calculating component values by hand, simulating, tweaking, and simulating repeatedly. A single nominal simulation often hides an important risk: real inductors and capacitors are rarely exactly their labeled values, so a design that looks perfect can fail in a fraction of real builds. This project automates the design loop and measures that risk.

## What it does

1. **Calculates** duty cycle, inductance, output capacitance, and current limits from a spec (Vin, Vout, Iout, switching frequency, ripple targets).
2. **Generates** an LTspice netlist from a Jinja2 template.
3. **Runs LTspice from Python** (via spicelib) and reads the measurements back from the simulation log.
4. **Compares** calculated and simulated values.
5. **Runs a Monte Carlo tolerance analysis**, simulating hundreds of randomized versions of the design.
6. **Sweeps output capacitance** to find the smallest value that meets a yield target, then confirms it with fresh random draws.

## Reference design

12 V to 5 V, 2 A, 500 kHz switching, 30% inductor ripple current, 50 mV output ripple target.
Calculated: duty cycle 0.417, inductor 9.72 µH, output capacitor 3.0 µF.

## Results

### Calculation vs simulation (nominal design)

| Quantity | Calculated | Simulated | Error |
|---|---|---|---|
| Average output voltage | 5.000 V | 4.947 V | -1.1% |
| Output ripple (pp) | 50.0 mV | 50.2 mV | +0.5% |
| Inductor ripple current (pp) | 0.600 A | 0.602 A | +0.3% |
| Inductor peak current | 2.300 A | 2.280 A | -0.9% |
| Inductor valley current | 1.700 A | 1.678 A | -1.3% |

The simulated efficiency is 98.8% (0.119 W lost), which matches a hand estimate of the I²R losses in the switch, diode, and inductor resistance (about 0.118 W). The 1.1% voltage shortfall comes from the voltage drops across those same resistances; the converter is open-loop, so nothing corrects it.

### Tolerance analysis

Each run randomizes the inductor (±20%), capacitor (±20%), capacitor ESR (±50%), inductor resistance (±20%), and switch resistance (±30%), uniformly across each band. A run passes if the average output voltage is within 4.85-5.15 V, ripple is at most 60 mV (20% above the design target), and inductor peak current is at most 2.5 A.

| Output capacitance | Runs | Passed | Yield |
|---|---|---|---|
| 3.0 µF (calculated value) | 100 | 85 | 85% |
| 3.6 µF | 300 | 296 | 98.7% |
| 3.9 µF | 300 | 299 | 99.7% |

Key findings:

- **The nominal design passes, but 15% of randomized builds fail.** Every failure was output ripple; voltage and peak current stayed within limits in all runs.
- **Ripple is set almost entirely by inductance × capacitance** (it scales as roughly 1 / (L × C)). Failures occur only when both parts land near the bottom of their tolerance bands. For this converter, L × C must stay above about 24.4 µH·µF for ripple to meet the 60 mV limit.
- **Small samples mislead.** A 100-run sweep showed 100% yield at 3.6 µF, but 300 fresh runs gave 98.7%. A result of zero failures in n runs only supports a failure rate below about 3/n, so each design was confirmed with independent random draws.
- **The one failure at 3.9 µF** (60.3 mV) is the theoretical worst-case corner, with both L and C at -20%. Passing every corner by construction would need roughly 1.31 times the calculated capacitance or more.

## Limitations

- **Simulation only.** No physical prototype was built, so results are not validated against hardware.
- **Open-loop.** There is no feedback controller, so input-voltage and load variation were not analyzed.
- **Idealized semiconductors.** An ideal diode stands in for the low-side switch, and there are no switching, gate-drive, or dead-time losses. The 98.8% efficiency is therefore optimistic.
- **Simplified capacitor model.** No DC-bias derating, and no temperature or aging effects.
- **Assumed distributions and limits.** Tolerances are sampled uniformly (pessimistic compared with real parts), and the pass limits are my own choices for this reference design.

## How to run

Requires Windows, Python 3.13, and LTspice (tested with LTspice 26.1.1).

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
python run_step3_demo.py        # simulate and compare with calculations
python run_step4_demo.py        # Monte Carlo tolerance analysis
python run_step5_demo.py        # capacitance sweep and confirmation
python run_step5b_confirm.py    # confirm the 3.9 µF design
```

If the code cannot find LTspice, set the `LTSPICE_EXE` environment variable to the full path of `LTspice.exe`, or add the path to `find_ltspice()` in `src/buckdesign/simulate.py`.

## Project structure

```
src/buckdesign/
    specification.py   input spec and validation
    calc.py            design formulas
    netlist.py         renders the LTspice netlist
    simulate.py        runs LTspice, parses measurements
    compare.py         calculated vs simulated
    tolerance.py       Monte Carlo analysis
    sweep.py           capacitance sweep
    report.py          CSV and figure output
templates/buck.cir.j2  netlist template
tests/                 29 automated tests
reports/               result figures and CSV files
```

## Figures

- `reports/montecarlo_12v_5v_2a.png`: tolerance analysis at 3.0 µF
- `reports/confirm_montecarlo.png`: confirmation run at 3.6 µF
- `reports/confirm_39uF.png`: confirmation run at 3.9 µF