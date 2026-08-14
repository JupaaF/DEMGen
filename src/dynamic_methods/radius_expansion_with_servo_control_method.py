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

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

from dynamic_methods.dynamic_method import DynamicMethod
from data_processing.pre_processing import create_particles_inside_of_a_domain
from data_processing.pre_processing.particle_case_request import (
    ParticleCaseRequest,
    ParticleGenerationContext,
)


@dataclass(frozen=True)
class Attempt:
    case_number: int
    packing_density: float

class RadiusExpansionWithServoControlMethod(DynamicMethod):

    def __init__(self) -> None:
        super().__init__()

    def CreateInitialCases(self, attempt, initial_case_creator):
        initial_case_creator.create_case(
            ParticleCaseRequest(
                case_number=attempt.case_number,
                output_file_name='inletPGDEM_ini.mdpa',
                packing_density=attempt.packing_density,
            )
        )

    def RunDEM(self, attempt):

        if attempt.is_final_attempt:
            script_name = "radius_expansion_with_servo_control_method_run_final.py"
        else:
            script_name = "radius_expansion_with_servo_control_method_run.py"

        return self._run_case_script(script_name, attempt)

    def _run_case_script(self, script_name, attempt):

        case_path = Path(self.run_path) / "generated_cases" / f"case_{attempt.case_number}"
        script_path = Path(self.ini_path) / "src" / "utilities" / script_name
        case_parameters_path = case_path / "demgen_case_parameters.json"
        subprocess.run(
            [sys.executable, script_path, "--case-parameters", case_parameters_path],
            cwd=case_path,
            check=True,
        )
        return (case_path / "success.txt").is_file()

    def Run(self, parameters, ini_path, run_path):

        self.Initialization(parameters, ini_path, run_path)
        generation = self.parameters["random_particle_generation_parameters"]
        packing_num = self.parameters["packing_num"]
        attempt_densities = self.GetAttemptDensities(generation)

        if not attempt_densities:
            raise ValueError("packing_density_delta_list must contain at least one value.")

        uses_seed = any(
            str(value).lower() == "true"
            for value in (
                generation.get("DO_USE_SEED", False),
                generation["random_variable_settings"].get("do_use_seed", False),
            )
        )
        if uses_seed and packing_num > 1:
            raise ValueError(
                "A seed cannot be used when packing_num is greater than one."
            )

        initial_case_creator = create_particles_inside_of_a_domain.CreateParticlesInsideOfADomain(
            ParticleGenerationContext(
                parameters=self.parameters,
                project_root=Path(self.ini_path),
                run_dir=Path(self.run_path),
            )
        )
        marker_path = Path(self.run_path) / "generation_marker.txt"
        marker_path.unlink(missing_ok=True)

        for case_number in range(1, packing_num + 1):
            for attempt_index, packing_density in enumerate(attempt_densities):
                attempt = Attempt(
                    case_number=case_number,
                    packing_density=packing_density,
                )
                with marker_path.open("a") as marker_file:
                    marker_file.write(
                        f"Generation {attempt.case_number} - {attempt.packing_density}\n"
                    )
                self.CreateInitialCases(attempt, initial_case_creator)
                if self.RunDEM(attempt):
                    break

    def GetAttemptDensities(self, generation):
        return [
            generation["target_packing_density"] - delta
            for delta in generation["packing_density_delta_list"]
        ]
