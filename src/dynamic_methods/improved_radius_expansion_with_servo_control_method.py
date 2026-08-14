#/////////////////////////////////////////////////
__author__      = "Chengshun Shang (CIMNE)"
__copyright__   = "Copyright (C) 2023-present by Chengshun Shang"
__version__     = "1.0.1"
__maintainer__  = "Chengshun Shang"
__email__       = "cshang@cimne.upc.edu"
__status__      = "development"
__date__        = "June 05, 2025"
__license__     = "BSD 2-Clause License"
#/////////////////////////////////////////////////

from pathlib import Path

from dynamic_methods.radius_expansion_with_servo_control_method import RadiusExpansionWithServoControlMethod
from curve_generation import SINGLE_POINT, load_curve_generation_settings

class ImprovedRadiusExpansionWithServoControlMethod(RadiusExpansionWithServoControlMethod):
    
    def __init__(self) -> None:
        super().__init__()

    def RunDEM(self, attempt):
        script_name = "improved_radius_expansion_with_servo_control_method_run.py"

        return self._run_case_script(script_name, attempt)

    def GetAttemptDensities(self, generation):
        settings = load_curve_generation_settings(
            self.parameters,
            Path(self.run_path) / "ProjectParametersDEM.json",
        )
        if settings.mode == SINGLE_POINT:
            return [
                settings.generation_density - delta
                for delta in generation["packing_density_delta_list"]
            ]
        return [settings.generation_density]
