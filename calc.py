from dataclasses import dataclass

from .specification import BuckSpec


def duty_cycle(vin: float, vout: float) -> float:
    return vout / vin


def inductor_ripple_current(iout: float, ripple_current_ratio: float) -> float:
    return ripple_current_ratio * iout


def inductance(vin: float, vout: float, fsw: float, delta_il: float) -> float:
    return vout * (vin - vout) / (vin * fsw * delta_il)


def output_capacitance(delta_il: float, fsw: float, delta_v: float) -> float:
    return delta_il / (8 * fsw * delta_v)


def critical_load_current(delta_il: float) -> float:
    return delta_il / 2


@dataclass(frozen=True)
class BuckDesign:

    duty: float             
    delta_il: float         
    inductance: float       
    capacitance: float      
    il_peak: float          
    il_valley: float        
    i_crit: float           

def design_buck(spec: BuckSpec) -> BuckDesign:
    d = duty_cycle(spec.vin, spec.vout)
    delta_il = inductor_ripple_current(spec.iout, spec.ripple_current_ratio)
    return BuckDesign(
        duty=d,
        delta_il=delta_il,
        inductance=inductance(spec.vin, spec.vout, spec.fsw, delta_il),
        capacitance=output_capacitance(delta_il, spec.fsw, spec.ripple_voltage_pp),
        il_peak=spec.iout + delta_il / 2,
        il_valley=spec.iout - delta_il / 2,
        i_crit=critical_load_current(delta_il),
    )