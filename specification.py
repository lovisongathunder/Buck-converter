from dataclasses import dataclass


@dataclass(frozen=True)
class BuckSpec:
 
    vin: float                         
    vout: float                        
    iout: float                        
    fsw: float                         
    ripple_current_ratio: float = 0.3  
    ripple_voltage_pp: float = 0.05    

    def __post_init__(self):
        for name in ("vin", "vout", "iout", "fsw", "ripple_voltage_pp"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive, got {getattr(self, name)}")
        if self.vout >= self.vin:
            raise ValueError(
                f"A buck converter steps voltage down: vout ({self.vout} V) "
                f"must be lower than vin ({self.vin} V)"
            )
        if not 0 < self.ripple_current_ratio <= 1:
            raise ValueError(
                "ripple_current_ratio must be between 0 and 1 "
                f"(typical: 0.2 to 0.4), got {self.ripple_current_ratio}"
            )