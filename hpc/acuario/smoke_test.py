from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
UTILITIES_ROOT = SRC_ROOT / "utilities"
for source_path in (SRC_ROOT, UTILITIES_ROOT):
    if str(source_path) not in sys.path:
        sys.path.insert(0, str(source_path))

import KratosMultiphysics

from data_processing.pre_processing.create_cyclic_stress_controlled_particles import (
    CreateCyclicStressControlledParticles,
)
from data_processing.pre_processing.particle_case_request import (
    ParticleGenerationContext,
)
from demgen_case_parameters import load_case_parameters
from utilities.cyclic_stress_controlled_method_run import (
    CyclicStressControlledAnalysis,
)


RUN_DIRECTORY = (
    PROJECT_ROOT / "simulation_runs" / "cyclic_stress_10kPa_density_0.64"
)
SMOKE_FINAL_TIME = 1.0e-3


def main() -> None:
    parameters = json.loads(
        (RUN_DIRECTORY / "ParametersDEMGen.json").read_text(encoding="utf-8")
    )
    with tempfile.TemporaryDirectory(prefix="demgen-smoke-") as temporary_name:
        temporary_path = Path(temporary_name)
        for filename in ("ProjectParametersDEM.json", "MaterialsDEM.json"):
            shutil.copyfile(RUN_DIRECTORY / filename, temporary_path / filename)

        creator = CreateCyclicStressControlledParticles(
            ParticleGenerationContext(
                parameters=parameters,
                project_root=PROJECT_ROOT,
                run_dir=temporary_path,
            )
        )
        case_path = creator.create_case(1)
        case_parameters = load_case_parameters(
            case_path / "demgen_case_parameters.json"
        )
        project_parameters = json.loads(
            (case_path / "ProjectParametersDEM.json").read_text(encoding="utf-8")
        )
        project_parameters["FinalTime"] = SMOKE_FINAL_TIME

        original_directory = Path.cwd()
        try:
            os.chdir(case_path)
            analysis = CyclicStressControlledAnalysis(
                KratosMultiphysics.Model(),
                KratosMultiphysics.Parameters(json.dumps(project_parameters)),
                case_parameters,
            )
            analysis.Run()
        finally:
            os.chdir(original_directory)

    print("Acuario smoke test completed successfully.", flush=True)


if __name__ == "__main__":
    main()

