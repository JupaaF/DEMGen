#/////////////////////////////////////////////////
__author__      = "Chengshun Shang (CIMNE)"
__copyright__   = "Copyright (C) 2023-present by Chengshun Shang"
__version__     = "0.0.1"
__maintainer__  = "Chengshun Shang"
__email__       = "cshang@cimne.upc.edu"
__status__      = "development"
__date__        = "June 26, 2024"
__license__     = "BSD 2-Clause License"
#/////////////////////////////////////////////////

from pathlib import Path
import subprocess
import sys

from dynamic_methods.dynamic_method import DynamicMethod
from data_processing.pre_processing import create_particles_inside_of_a_domain
from data_processing.pre_processing.particle_case_request import (
    ParticleCaseRequest,
    ParticleGenerationContext,
)

class RadiusExpansionMethod(DynamicMethod):

    def __init__(self) -> None:

        pass

    def CreateInitialCases(self):

        initial_case_creator = create_particles_inside_of_a_domain.CreateParticlesInsideOfADomain(
            ParticleGenerationContext(
                parameters=self.parameters,
                project_root=Path(self.ini_path),
                run_dir=Path(self.run_path),
            )
        )
        packing_num = self.parameters["packing_num"]
        aim_file_name = 'inletPGDEM_ini.mdpa'

        for case_number in range(1, packing_num + 1):
            initial_case_creator.create_case(
                ParticleCaseRequest(
                    case_number=case_number,
                    output_file_name=aim_file_name,
                )
            )

    def RunDEM(self):

        for case_number in range(1, self.parameters["packing_num"] + 1):
            case_path = Path(self.run_path) / "generated_cases" / f"case_{case_number}"
            subprocess.run(
                [sys.executable, "radius_expansion_method_run_v1.4.py"],
                cwd=case_path,
                check=True,
            )
