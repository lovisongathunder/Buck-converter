from dataclasses import dataclass, replace

from .calc import BuckDesign
from .specification import BuckSpec
from .tolerance import PassCriteria, Tolerances, run_monte_carlo


@dataclass(frozen=True)
class SweepPoint:
    scale: float             
    capacitance: float       
    yield_fraction: float   
    records: list


def sweep_capacitance(
    spec: BuckSpec,
    design: BuckDesign,
    tol: Tolerances,
    criteria: PassCriteria,
    scales: list,
    n: int = 100,
    seed: int = 1,
    folder: str = "sims/sweep",
) -> list:
    points = []
    for k in scales:
        sized = replace(design, capacitance=design.capacitance * k)
        records = run_monte_carlo(
            spec, sized, tol, criteria, n=n, seed=seed,
            folder=f"{folder}/c_{k:.2f}", progress=False,
        )
        point = SweepPoint(k, sized.capacitance,
                           sum(r.passed for r in records) / n, records)
        print(f"C x{k:.2f} ({sized.capacitance * 1e6:.2f} uF): "
              f"yield {point.yield_fraction * 100:.0f} %")
        points.append(point)
    return points


def smallest_passing(points: list, target: float):
    ok = [p for p in points if p.yield_fraction >= target]
    return min(ok, key=lambda p: p.scale) if ok else None