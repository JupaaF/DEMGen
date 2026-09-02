from pathlib import Path
import subprocess
import sys

from data_processing.pre_processing.create_cyclic_stress_controlled_particles import (
    CreateCyclicStressControlledParticles,
)
from data_processing.pre_processing.particle_case_request import (
    ParticleGenerationContext,
)
from dynamic_methods.dynamic_method import DynamicMethod


class CyclicStressControlledMethod(DynamicMethod):
    def CreateInitialCases(self):
        packing_num = self.parameters.get("packing_num")
        if (
            isinstance(packing_num, bool)
            or not isinstance(packing_num, int)
            or packing_num < 1
        ):
            raise ValueError("packing_num must be an integer greater than zero.")
        creator = CreateCyclicStressControlledParticles(
            ParticleGenerationContext(
                parameters=self.parameters,
                project_root=Path(self.ini_path),
                run_dir=Path(self.run_path),
            )
        )
        for case_number in range(1, packing_num + 1):
            creator.create_case(case_number)

    def RunDEM(self):
        script_path = (
            Path(self.ini_path)
            / "src"
            / "utilities"
            / "cyclic_stress_controlled_method_run.py"
        )
        for case_number in range(1, self.parameters["packing_num"] + 1):
            case_path = (
                Path(self.run_path)
                / "generated_cases"
                / f"case_{case_number}"
            )
            subprocess.run(
                [
                    sys.executable,
                    script_path,
                    "--case-parameters",
                    case_path / "demgen_case_parameters.json",
                ],
                cwd=case_path,
                check=True,
            )
