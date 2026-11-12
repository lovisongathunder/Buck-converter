from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .calc import BuckDesign
from .specification import BuckSpec

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"

_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    undefined=StrictUndefined,  
    keep_trailing_newline=True,
)


def _num(x: float) -> str:
    return f"{x:.6g}"


def render_netlist(
    spec: BuckSpec,
    design: BuckDesign,
    *,
    ron: float = 0.01,           
    dcr: float = 0.02,           
    esr: float = 0.005,          
    n_cycles: int = 400,         
    n_meas_cycles: int = 20,     
    steps_per_cycle: int = 200,  
) -> str:
    period = 1 / spec.fsw
    context = {
        "vin": _num(spec.vin),
        "vout": _num(spec.vout),
        "iout": _num(spec.iout),
        "fsw_khz": _num(spec.fsw / 1e3),
        "duty": _num(design.duty),
        "period": _num(period),
        "t_on": _num(design.duty * period),
        "t_edge": "1n",
        "inductance": _num(design.inductance),
        "capacitance": _num(design.capacitance),
        "rload": _num(spec.vout / spec.iout),
        "ron": _num(ron),
        "dcr": _num(dcr),
        "esr": _num(esr),
        "t_stop": _num(n_cycles * period),
        "t_meas": _num((n_cycles - n_meas_cycles) * period),
        "n_meas_cycles": n_meas_cycles,
        "max_step": _num(period / steps_per_cycle),
    }
    return _env.get_template("buck.cir.j2").render(**context)


def write_netlist(netlist: str, path) -> Path:
    """Save the netlist, creating the folder if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(netlist)
    return path