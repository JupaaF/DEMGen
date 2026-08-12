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

from dynamic_methods.radius_expansion_with_servo_control_method import RadiusExpansionWithServoControlMethod

class ImprovedRadiusExpansionWithServoControlMethod(RadiusExpansionWithServoControlMethod):
    
    def __init__(self) -> None:
        super().__init__()

    def RunDEM(self, attempt):

        if attempt.is_final_attempt:
            script_name = "improved_radius_expansion_with_servo_control_method_run_final.py"
        else:
            script_name = "improved_radius_expansion_with_servo_control_method_run.py"

        return self._run_case_script(script_name, attempt)
