#/////////////////////////////////////////////////
__author__      = "Chengshun Shang (CIMNE)"
__copyright__   = "Copyright (C) 2023-present by Chengshun Shang"
__version__     = "1.1.0"
__maintainer__  = "Chengshun Shang"
__email__       = "cshang@cimne.upc.edu"
__status__      = "development"
__date__        = "June 20, 2024"
__license__     = "BSD 2-Clause License"
#/////////////////////////////////////////////////

import argparse
import json
import os
from pathlib import Path

class DEMGenMainFramework():

    def __init__(self) -> None:
        
        print('-'*76 + '\n')

    ####################main processes#############################################
    def Initilization(self, aim_path):
        
        #read parameter.json file
        #file_path = self.choose_file()
        file_path = aim_path
        
        if file_path:
            self.set_working_directory(file_path)
            self.parameters = self.read_json(file_path)
        else:
            print("No file selected")
            exit(0)

    def GenerationRun(self):
        
        #particle packing generation
        if self.parameters["generator_name"] == "gravitational_deposition_method":

            from .dynamic_methods import gravitational_deposition_method
            MyDEM = gravitational_deposition_method.GravitationalDepositionMethod()
            MyDEM.Run(self.parameters, self.ini_path)

        elif self.parameters["generator_name"] == "isotropic_compression_method":
            
            from .dynamic_methods import isotropic_compression_method
            MyDEM = isotropic_compression_method.IsotropicCompressionMethod()
            MyDEM.Run(self.parameters, self.ini_path)

        elif self.parameters["generator_name"] == "radius_expansion_method":
            
            from .dynamic_methods import radius_expansion_method
            MyDEM = radius_expansion_method.RadiusExpansionMethod()
            MyDEM.Run(self.parameters, self.ini_path)

        elif self.parameters["generator_name"] == "radius_expansion_with_servo_control_method":
            
            from .dynamic_methods import radius_expansion_with_servo_control_method
            MyDEM = radius_expansion_with_servo_control_method.RadiusExpansionWithServoControlMethod()
            MyDEM.Run(self.parameters, self.ini_path)

        elif self.parameters["generator_name"] == "improved_radius_expansion_with_servo_control_method":

            from .dynamic_methods import improved_radius_expansion_with_servo_control_method
            MyDEM = improved_radius_expansion_with_servo_control_method.ImprovedRadiusExpansionWithServoControlMethod()
            MyDEM.Run(self.parameters, self.ini_path)

        elif self.parameters["generator_name"] == "cubic_arrangement_method":

            from .constructive_methods import cubic_arrangement_method
            MyDEM = cubic_arrangement_method.CubicArrangementMethod()
            MyDEM.Run(self.parameters, self.ini_path)

        elif self.parameters["generator_name"] == "hpc_arrangement_method":

            from .constructive_methods import hpc_arrangement_method
            MyDEM = hpc_arrangement_method.HpcArrangementMethod()
            MyDEM.Run(self.parameters, self.ini_path)
        
        else:
            print("No (or wrong) generator name given")

        #what we get from above processes is a .mdpa file of DEM particles

    def CharacterizationRun(self):

        print("Start particle packing characterization...")
        #particle packing characterization
        if self.parameters["packing_charcterization_option"] is True:
            
            if self.parameters["regular_shape_option"] is True:

                if self.parameters["packing_num"] > 1:
                    from .data_processing.post_processing import packing_characterization_multi
                    MyDEMChara = packing_characterization_multi.PackingCharacterizationMulti()
                    MyDEMChara.Run(self.parameters, self.ini_path)
                else:
                    from .data_processing.post_processing import packing_characterization_single
                    MyDEMChara = packing_characterization_single.PackingCharacterizationSingle()
                    MyDEMChara.Run(self.parameters, self.ini_path)
            
            else:
                pass
        else:
            print("No packing analysis has been done because [packing_charcterization_option] is set as [False]")

        print("Particle packing characterization finished.")

    def Finalization(self):
        
        print("Successfully finish!")

    ####################detail functions################################################
    def set_working_directory(self, file_path):

        self.ini_path = os.path.dirname(os.path.abspath(__file__))

        directory = os.path.dirname(file_path)
        os.chdir(directory)
        print(f"Set current working directory: {os.getcwd()}")

    def read_json(self, file_path):

        with open(file_path, 'r') as file:
            parameters = json.load(file)
        return parameters


def build_argument_parser():
    parser = argparse.ArgumentParser(
        prog="demgen",
        description="Generate and characterize DEM particle packings.",
    )
    parser.add_argument(
        "parameters",
        nargs="?",
        default="ParametersDEMGen.json",
        help="path to ParametersDEMGen.json (default: file in the current directory)",
    )
    return parser


def main(argv=None):
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    parameters_path = Path(args.parameters).expanduser().resolve()

    if not parameters_path.is_file():
        parser.error(f"parameter file not found: {parameters_path}")

    demgen = DEMGenMainFramework()
    demgen.Initilization(str(parameters_path))
    demgen.GenerationRun()
    demgen.CharacterizationRun()
    demgen.Finalization()


if __name__ == "__main__":
    main()
    
