import os
import re
from dataclasses import dataclass
from pathlib import Path

from .calc import BuckDesign
from .netlist import render_netlist, write_netlist
from .specification import BuckSpec


_MEAS_LINE = re.compile(
    r"^(\w+):\s+.+?=\s*([-+]?\d[\d.]*(?:[eE][-+]?\d+)?)(?:\s+FROM\b|\s*$)",
    re.MULTILINE,
)


@dataclass(frozen=True)
class SimResult:

    vout_avg: float   
    vout_pp: float    
    il_max: float     
    il_min: float     
    pin: float        
    pout: float       
    eff: float        

    @property
    def il_pp(self) -> float:
        """Inductor ripple current, peak-to-peak (A)."""
        return self.il_max - self.il_min


def read_log_text(path) -> str:
    data = Path(path).read_bytes()
    if data[:2] in (b"\xff\xfe", b"\xfe\xff") or data[1:2] == b"\x00":
        return data.decode("utf-16", errors="replace")
    return data.decode("utf-8", errors="replace")


def parse_measurements(log_text: str) -> dict:
    return {name: float(value) for name, value in _MEAS_LINE.findall(log_text)}


def result_from_log(log_text: str) -> SimResult:
    values = parse_measurements(log_text)
    needed = ("vout_avg", "vout_pp", "il_max", "il_min", "pin", "pout", "eff")
    missing = [name for name in needed if name not in values]
    if missing:
        raise ValueError(
            f"Measurements missing from the LTspice log: {', '.join(missing)}. "
            "Open the .cir file in LTspice and check the error log."
        )
    return SimResult(**{name: values[name] for name in needed})


def find_ltspice():
    from_env = os.environ.get("LTSPICE_EXE")
    if from_env and Path(from_env).is_file():
        return Path(from_env)

    local = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", "")
    candidates = [
        Path(r"E:\LTspice\LTspice.exe"),
        Path(local) / "Programs" / "ADI" / "LTspice" / "LTspice.exe",
        Path(program_files) / "ADI" / "LTspice" / "LTspice.exe",
        Path(program_files) / "LTC" / "LTspiceXVII" / "XVIIx64.exe",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def run_netlist(netlist_path: str | Path, output_folder: str | Path = "sims/runs") -> Path:
    from spicelib import SimRunner
    from spicelib.simulators.ltspice_simulator import LTspice

    exe = find_ltspice()
    if exe is None:
        raise RuntimeError(
            "Could not find LTspice.exe. Set the LTSPICE_EXE environment variable "
            "to its full path, for example:\n"
            '  $env:LTSPICE_EXE = "C:\\path\\to\\LTspice.exe"'
        )
    simulator = LTspice.create_from(str(exe))

    runner = SimRunner(simulator=simulator, output_folder=str(output_folder))
    _raw, log = runner.run_now(netlist_path)
    if log is None or not Path(log).exists():
        raise RuntimeError(
        )
    return Path(log)


def simulate_design(
    spec: BuckSpec,
    design: BuckDesign,
    name: str = "buck",
    sims_folder: str | Path = "sims",
    **netlist_options,
) -> SimResult:
    sims_folder = Path(sims_folder)
    netlist = render_netlist(spec, design, **netlist_options)
    cir_path = write_netlist(netlist, sims_folder / f"{name}.cir")
    log_path = run_netlist(cir_path, output_folder=sims_folder / "runs")
    return result_from_log(read_log_text(log_path))