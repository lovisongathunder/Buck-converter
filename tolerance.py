"""Monte Carlo tolerance analysis: simulate many randomized copies of a design."""

from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from .calc import BuckDesign
from .netlist import render_netlist, write_netlist
from .simulate import SimResult, read_log_text, result_from_log, run_netlist
from .specification import BuckSpec

# Nominal parasitics. Keep these equal to the defaults in netlist.render_netlist.
NOMINAL_ESR = 0.005   # output capacitor ESR (ohm)
NOMINAL_DCR = 0.02    # inductor series resistance (ohm)
NOMINAL_RON = 0.01    # switch on-resistance (ohm)


@dataclass(frozen=True)
class Tolerances:
    """How far each part may stray from nominal, as a fraction (0.20 = +/-20 %)."""

    inductance: float = 0.20
    capacitance: float = 0.20
    esr: float = 0.50
    dcr: float = 0.20
    ron: float = 0.30


@dataclass(frozen=True)
class PassCriteria:
    """Limits a run must meet to count as passing."""

    vout_min: float      # lowest acceptable average output voltage (V)
    vout_max: float      # highest acceptable average output voltage (V)
    vout_pp_max: float   # largest acceptable output ripple, peak-to-peak (V)
    il_peak_max: float   # largest acceptable inductor peak current (A)

    def failures(self, r: SimResult) -> list:
        """Return a list of the limits this result breaks (empty means pass)."""
        out = []
        if not self.vout_min <= r.vout_avg <= self.vout_max:
            out.append("Output voltage outside window")
        if r.vout_pp > self.vout_pp_max:
            out.append("Output ripple too high")
        if r.il_max > self.il_peak_max:
            out.append("Inductor peak current too high")
        return out


@dataclass(frozen=True)
class Sample:
    """One randomized set of part values."""

    inductance: float
    capacitance: float
    esr: float
    dcr: float
    ron: float


@dataclass(frozen=True)
class RunRecord:
    """Outcome of one Monte Carlo run."""

    index: int
    sample: Sample
    result: SimResult
    failures: list

    @property
    def passed(self) -> bool:
        return not self.failures


def draw_samples(design: BuckDesign, tol: Tolerances, n: int, seed: int = 1) -> list:
    """Draw n random part sets, uniform across each tolerance band.

    Uniform sampling is pessimistic compared with real parts, which cluster near
    nominal, so the yield it reports is on the cautious side.
    """
    rng = np.random.default_rng(seed)

    def spread(nominal: float, fraction: float):
        return nominal * rng.uniform(1 - fraction, 1 + fraction, n)

    inductance = spread(design.inductance, tol.inductance)
    capacitance = spread(design.capacitance, tol.capacitance)
    esr = spread(NOMINAL_ESR, tol.esr)
    dcr = spread(NOMINAL_DCR, tol.dcr)
    ron = spread(NOMINAL_RON, tol.ron)
    return [
        Sample(float(a), float(b), float(c), float(d), float(e))
        for a, b, c, d, e in zip(inductance, capacitance, esr, dcr, ron)
    ]


def run_monte_carlo(
    spec: BuckSpec,
    design: BuckDesign,
    tol: Tolerances,
    criteria: PassCriteria,
    n: int = 100,
    seed: int = 1,
    folder="sims/montecarlo",
    progress: bool = True,
) -> list:
    """Simulate n randomized versions of the design in LTspice."""
    folder = Path(folder)
    records = []
    for i, s in enumerate(draw_samples(design, tol, n, seed)):
        varied = replace(design, inductance=s.inductance, capacitance=s.capacitance)
        netlist = render_netlist(spec, varied, ron=s.ron, dcr=s.dcr, esr=s.esr)
        cir_path = write_netlist(netlist, folder / f"run_{i:03d}.cir")
        log_path = run_netlist(cir_path, output_folder=folder / "runs")
        result = result_from_log(read_log_text(log_path))
        _delete_waveforms(log_path)

        record = RunRecord(i, s, result, criteria.failures(result))
        records.append(record)
        if progress:
            status = "pass" if record.passed else "FAIL: " + ", ".join(record.failures)
            print(f"run {i + 1:>3}/{n}  ripple {result.vout_pp * 1e3:5.1f} mV  {status}")
    return records


def _delete_waveforms(log_path) -> None:
    """Remove the large .raw waveform files; the log holds everything we need."""
    log_path = Path(log_path)
    for raw in log_path.parent.glob(f"{log_path.stem}*.raw"):
        raw.unlink(missing_ok=True)


def summarize(records: list) -> str:
    """Plain-text summary: yield, what failed, and the spread of key results."""
    n = len(records)
    passed = sum(1 for r in records if r.passed)
    lines = [f"Runs: {n}", f"Passed: {passed} ({passed / n * 100:.0f} %)"]

    counts = Counter(f for r in records for f in r.failures)
    for reason, count in counts.most_common():
        lines.append(f"  {reason}: {count} runs")

    def row(label, values):
        v = np.asarray(values)
        return f"{label:<26}{v.min():>10.3f}{v.mean():>10.3f}{v.max():>10.3f}"

    lines += [
        "",
        f"{'':<26}{'min':>10}{'mean':>10}{'max':>10}",
        row("Output voltage (V)", [r.result.vout_avg for r in records]),
        row("Output ripple (mV)", [r.result.vout_pp * 1e3 for r in records]),
        row("Inductor peak (A)", [r.result.il_max for r in records]),
        row("Efficiency (%)", [r.result.eff * 100 for r in records]),
    ]
    return "\n".join(lines)