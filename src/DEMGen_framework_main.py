#/////////////////////////////////////////////////
__author__      = "Chengshun Shang (CIMNE)"
__copyright__   = "Copyright (C) 2023-present by Chengshun Shang"
__version__     = "0.0.1"
__maintainer__  = "Chengshun Shang"
__email__       = "cshang@cimne.upc.edu"
__status__      = "development"
__date__        = "June 20, 2024"
__license__     = "BSD 2-Clause License"
#/////////////////////////////////////////////////

import json
import argparse
from pathlib import Path

class DEMGenMainFramework():

    def __init__(self) -> None:
        
        print('-'*76 + '\n')

    # ----------------- Main Process ----------------- #

    def Initilization(self, parameters_path):

        self.parameters_path = Path(parameters_path).expanduser().resolve()
        self.set_paths()
        self.read_json(self.parameters_path)

    def GenerationRun(self):
        
        #particle packing generation
        if self.parameters["generator_name"] == "gravitational_deposition_method":

            from dynamic_methods import gravitational_deposition_method
            MyDEM = gravitational_deposition_method.GravitationalDepositionMethod()
            MyDEM.Run(self.parameters, self.ini_path, self.run_path)

        elif self.parameters["generator_name"] == "isotropic_compression_method":
            
            from dynamic_methods import isotropic_compression_method
            MyDEM = isotropic_compression_method.IsotropicCompressionMethod()
            MyDEM.Run(self.parameters, self.ini_path, self.run_path)

        elif self.parameters["generator_name"] == "radius_expansion_method":
            
            from dynamic_methods import radius_expansion_method
            MyDEM = radius_expansion_method.RadiusExpansionMethod()
            MyDEM.Run(self.parameters, self.ini_path, self.run_path)

        elif self.parameters["generator_name"] == "radius_expansion_with_servo_control_method":
            
            from src.dynamic_methods import radius_expansion_with_servo_control_method
            MyDEM = radius_expansion_with_servo_control_method.RadiusExpansionWithServoControlMethod()
            MyDEM.Run(self.parameters, self.ini_path, self.run_path)

        elif self.parameters["generator_name"] == "improved_radius_expansion_with_servo_control_method":

            from dynamic_methods import improved_radius_expansion_with_servo_control_method
            MyDEM = improved_radius_expansion_with_servo_control_method.ImprovedRadiusExpansionWithServoControlMethod()
            MyDEM.Run(self.parameters, self.ini_path, self.run_path)

        elif self.parameters["generator_name"] == "cyclic_stress_controlled_method":

            from dynamic_methods import cyclic_stress_controlled_method
            MyDEM = cyclic_stress_controlled_method.CyclicStressControlledMethod()
            MyDEM.Run(self.parameters, self.ini_path, self.run_path)

        elif self.parameters["generator_name"] == "cubic_arrangement_method":

            from constructive_methods import cubic_arrangement_method
            MyDEM = cubic_arrangement_method.CubicArrangementMethod()
            MyDEM.Run(self.parameters, self.ini_path, self.run_path)

        elif self.parameters["generator_name"] == "hpc_arrangement_method":

            from constructive_methods import hpc_arrangement_method
            MyDEM = hpc_arrangement_method.HpcArrangementMethod()
            MyDEM.Run(self.parameters, self.ini_path, self.run_path)
        
        else:
            print("No (or wrong) generator name given")

        #what we get from above processes is a .mdpa file of DEM particles

    def CharacterizationRun(self):

        print("Start particle packing characterization...")
        #particle packing characterization
        if self.parameters["packing_charcterization_option"] is True:
            
            if self.parameters["regular_shape_option"] is True:

                if self.parameters["packing_num"] > 1:
                    from data_processing.post_processing import packing_characterization_multi
                    MyDEMChara = packing_characterization_multi.PackingCharacterizationMulti()
                    MyDEMChara.Run(self.parameters, self.ini_path, self.run_path)
                else:
                    from data_processing.post_processing import packing_characterization_single
                    MyDEMChara = packing_characterization_single.PackingCharacterizationSingle()
                    MyDEMChara.Run(self.parameters, self.ini_path, self.run_path)
            
            else:
                pass
        else:
            print("No packing analysis has been done because [packing_charcterization_option] is set as [False]")

        print("Particle packing characterization finished.")

    def set_paths(self):
        """Resolve the paths used by a DEMGen run without changing the CWD."""

        self.ini_path = Path(__file__).resolve().parent.parent
        self.run_path = self.parameters_path.parent
        print(f"Run directory: {self.run_path}")

    def read_json(self, file_path):
        try:
            with open(file_path, 'r') as file:
                self.parameters = json.load(file)
        except:
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate and characterize a DEM particle packing."
    )
    parser.add_argument(
        "parameters_path",
        help="Path to the ParametersDEMGen JSON file.",
    )
    args = parser.parse_args()

    demgen = DEMGenMainFramework()
    demgen.Initilization(args.parameters_path)
    demgen.GenerationRun()
    demgen.CharacterizationRun()
