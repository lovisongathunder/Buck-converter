from dataclasses import dataclass

from .calc import BuckDesign
from .simulate import SimResult
from .specification import BuckSpec


@dataclass(frozen=True)
class Row:
    name: str
    unit: str
    calculated: float
    simulated: float

    @property
    def error_pct(self) -> float:
        """Simulated minus calculated, as a percentage of the calculated value."""
        return (self.simulated - self.calculated) / self.calculated * 100


def compare(spec: BuckSpec, design: BuckDesign, result: SimResult) -> list:
    """Line up each calculated value with its simulated counterpart."""
    return [
        Row("Average output voltage", "V", spec.vout, result.vout_avg),
        Row("Output voltage ripple (pp)", "V", spec.ripple_voltage_pp, result.vout_pp),
        Row("Inductor ripple current (pp)", "A", design.delta_il, result.il_pp),
        Row("Inductor peak current", "A", design.il_peak, result.il_max),
        Row("Inductor valley current", "A", design.il_valley, result.il_min),
    ]


def format_comparison(rows: list, result: SimResult) -> str:
    """Plain-text table, ready to print or paste into a write-up."""
    lines = [
        f"{'Quantity':<36}{'Calculated':>12}{'Simulated':>12}{'Error':>9}",
        "-" * 69,
    ]
    for r in rows:
        lines.append(
            f"{r.name + ' (' + r.unit + ')':<36}"
            f"{r.calculated:>12.4f}{r.simulated:>12.4f}{r.error_pct:>+8.1f}%"
        )
    lines.append("-" * 69)
    lines.append(f"Efficiency (simulated only): {result.eff * 100:.1f} %")
    lines.append(f"Power loss (simulated only): {result.pin - result.pout:.3f} W")
    return "\n".join(lines)