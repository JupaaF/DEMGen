from __future__ import annotations

import json
from pathlib import Path
import random
import shutil
import statistics
from typing import Any, Mapping

from cyclic_stress_control import (
    CHECKPOINT_STATE_FILENAME,
    CYCLIC_FINAL_TIME,
    CYCLIC_SERVO_LOADING_FREQUENCY_STEPS,
    CYCLIC_SERVO_VELOCITY_MAX,
    CYCLIC_TIME_STEP,
    INITIAL_PACKING_DENSITY,
    PARTICLE_COUNT,
    CyclicStressControlledSettings,
    ParticleRadiusDistribution,
    cubic_box_length_from_radii,
    generate_non_overlapping_periodic_positions,
)
from data_processing.pre_processing.particle_case_request import (
    ParticleGenerationContext,
)
from particles import ParticlePacking, SphericalParticle


class CreateCyclicStressControlledParticles:
    """Create a dilute, polydisperse initial state for the cyclic protocol."""

    def __init__(self, context: ParticleGenerationContext) -> None:
        self.context = context
        self.generated_cases_path = context.run_dir / "generated_cases"
        self.generated_cases_path.mkdir(parents=True, exist_ok=True)

    def create_case(self, case_number: int) -> Path:
        settings = CyclicStressControlledSettings.from_parameters(
            self.context.parameters
        )
        stability_tolerances = self._load_stability_tolerances()
        radius_distribution = self._load_particle_radius_distribution()
        case_path = self.generated_cases_path / f"case_{case_number}"
        if self._can_resume_case(case_path, settings, radius_distribution):
            self._synchronize_runtime_limits(case_path)
            print(
                "Reusing cyclic stress-controlled case "
                f"{case_number} from its latest checkpoint."
            )
            return case_path
        if case_path.exists():
            shutil.rmtree(case_path)
        case_path.mkdir()

        random_source = random.Random()
        particle_radii = radius_distribution.sample(
            PARTICLE_COUNT,
            random_source,
        )
        box_length = cubic_box_length_from_radii(particle_radii)
        project_parameters = self._copy_and_adapt_project_parameters(
            case_path,
            box_length,
            settings,
            statistics.median(particle_radii),
        )
        positions = generate_non_overlapping_periodic_positions(
            particle_radii=particle_radii,
            random_source=random_source,
        )
        particles = ParticlePacking(
            SphericalParticle(
                node_id=index,
                element_id=index,
                position=position,
                radius=radius,
            )
            for index, (position, radius) in enumerate(
                zip(positions, particle_radii),
                start=1,
            )
        )
        problem_name = _problem_name(project_parameters)
        particles.write_mdpa(
            case_path / f"{problem_name}DEM.mdpa"
        )
        self._copy_support_files(case_path)
        self._write_case_parameters(
            case_path,
            box_length,
            settings,
            project_parameters,
            stability_tolerances,
            radius_distribution,
            particle_radii,
        )
        print(
            "Created cyclic stress-controlled case "
            f"{case_number} with {len(particles)} particles, "
            f"initial density {INITIAL_PACKING_DENSITY}, and box length "
            f"{box_length:.12g} m; radius range "
            f"[{min(particle_radii):.12g}, {max(particle_radii):.12g}] m."
        )
        return case_path

    def _copy_and_adapt_project_parameters(
        self,
        case_path: Path,
        box_length: float,
        settings: CyclicStressControlledSettings,
        median_particle_radius: float,
    ) -> dict[str, Any]:
        source_path = self.context.run_dir / "ProjectParametersDEM.json"
        with source_path.open(encoding="utf-8") as source_file:
            project_parameters = json.load(source_file)

        half_length = 0.5 * box_length
        project_parameters.update(
            {
                "PeriodicDomainOption": True,
                "BoundingBoxOption": True,
                "AutomaticBoundingBoxOption": False,
                "BoundingBoxMaxX": half_length,
                "BoundingBoxMaxY": half_length,
                "BoundingBoxMaxZ": half_length,
                "BoundingBoxMinX": -half_length,
                "BoundingBoxMinY": -half_length,
                "BoundingBoxMinZ": -half_length,
                "BoundingBoxMoveOption": True,
                "BoundingBoxServoLoadingOption": True,
                "GravityX": 0.0,
                "GravityY": 0.0,
                "GravityZ": 0.0,
                "RadiusExpansionOption": False,
                "ShiftParticlesOption": True,
                "MaxTimeStep": CYCLIC_TIME_STEP,
                "FinalTime": CYCLIC_FINAL_TIME,
                "EnergyCalculationOption": False,
                "ContactMeshOption": True,
                "do_print_results_option": False,
            }
        )
        for output_name in (
            "PostBoundingBox",
            "PostLocalContactForce",
            "PostDisplacement",
            "PostRadius",
            "PostVelocity",
            "PostAngularVelocity",
            "PostElasticForces",
            "PostContactForces",
            "PostRigidElementForces",
            "PostStressStrainOption",
            "PostTangentialElasticForces",
            "PostTotalForces",
            "PostPressure",
            "PostShearStress",
            "PostSkinSphere",
            "PostNonDimensionalVolumeWear",
            "PostParticleMoment",
            "PostEulerAngles",
            "PostRollingResistanceMoment",
            "PostContactRadius",
        ):
            if output_name in project_parameters:
                project_parameters[output_name] = False
        # Kratos' global-stress measurement requires both flags even when
        # result-file output itself is disabled.
        project_parameters["ContactMeshOption"] = True
        project_parameters["PostStressStrainOption"] = True
        servo_settings = project_parameters.get("BoundingBoxServoLoadingSettings")
        if not isinstance(servo_settings, dict):
            raise ValueError(
                "ProjectParametersDEM.json must define "
                "BoundingBoxServoLoadingSettings."
            )
        servo_settings.update(
            {
                "BoundingBoxServoLoadingType": "isotropic",
                "BoundingBoxServoLoadingStress": [
                    settings.maximum_cycle_pressure
                ]
                * 3,
                "BoundingBoxServoLoadingFrequency": (
                    CYCLIC_SERVO_LOADING_FREQUENCY_STEPS
                ),
                "BoundingBoxServoLoadingVelocityMax": (
                    CYCLIC_SERVO_VELOCITY_MAX
                ),
                "MeanParticleDiameterD50": 2.0 * median_particle_radius,
            }
        )

        destination_path = case_path / "ProjectParametersDEM.json"
        with destination_path.open("w", encoding="utf-8") as destination_file:
            json.dump(project_parameters, destination_file, indent=2)
        return project_parameters

    @staticmethod
    def _can_resume_case(
        case_path: Path,
        settings: CyclicStressControlledSettings,
        radius_distribution: ParticleRadiusDistribution,
    ) -> bool:
        state_path = case_path / CHECKPOINT_STATE_FILENAME
        if not state_path.is_file():
            return False
        try:
            checkpoint = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        try:
            case_parameters = json.loads(
                (case_path / "demgen_case_parameters.json").read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, json.JSONDecodeError):
            return False
        restart_files = checkpoint.get("restart_files")
        restart_label = checkpoint.get("restart_label")
        safe_restart_paths = (
            isinstance(restart_files, list)
            and len(restart_files) == 6
            and all(
                isinstance(relative_path, str)
                and not Path(relative_path).is_absolute()
                and ".." not in Path(relative_path).parts
                for relative_path in restart_files
            )
        )
        return (
            checkpoint.get("version") == 1
            and checkpoint.get("settings") == settings.to_dict()
            and case_parameters.get("particle_radius_distribution")
            == radius_distribution.to_dict()
            and isinstance(restart_label, str)
            and bool(restart_label)
            and safe_restart_paths
            and all(
                (case_path / relative_path).is_file()
                for relative_path in restart_files
            )
        )

    @staticmethod
    def _synchronize_runtime_limits(case_path: Path) -> None:
        parameters_path = case_path / "ProjectParametersDEM.json"
        with parameters_path.open(encoding="utf-8") as parameters_file:
            project_parameters = json.load(parameters_file)
        project_parameters["MaxTimeStep"] = CYCLIC_TIME_STEP
        project_parameters["FinalTime"] = CYCLIC_FINAL_TIME
        servo_settings = project_parameters["BoundingBoxServoLoadingSettings"]
        servo_settings["BoundingBoxServoLoadingFrequency"] = (
            CYCLIC_SERVO_LOADING_FREQUENCY_STEPS
        )
        servo_settings["BoundingBoxServoLoadingVelocityMax"] = (
            CYCLIC_SERVO_VELOCITY_MAX
        )
        with parameters_path.open("w", encoding="utf-8") as parameters_file:
            json.dump(project_parameters, parameters_file, indent=2)

    def _copy_support_files(self, case_path: Path) -> None:
        shutil.copyfile(
            self.context.run_dir / "MaterialsDEM.json",
            case_path / "MaterialsDEM.json",
        )
        shutil.copyfile(
            self.context.project_root / "src" / "utilities" / "show_packing.py",
            case_path / "show_packing.py",
        )

    def _write_case_parameters(
        self,
        case_path: Path,
        box_length: float,
        settings: CyclicStressControlledSettings,
        project_parameters: Mapping[str, Any],
        stability_tolerances: tuple[float, float],
        radius_distribution: ParticleRadiusDistribution,
        particle_radii: tuple[float, ...],
    ) -> None:
        unbalanced_force_tolerance, stress_tolerance = stability_tolerances
        case_parameters = {
            "cyclic_stress_controlled": settings.to_dict(),
            "particle_count": PARTICLE_COUNT,
            "particle_radius_distribution": radius_distribution.to_dict(),
            "minimum_particle_radius": min(particle_radii),
            "maximum_particle_radius": max(particle_radii),
            "mean_particle_radius": statistics.fmean(particle_radii),
            "median_particle_radius": statistics.median(particle_radii),
            "initial_packing_density": INITIAL_PACKING_DENSITY,
            "initial_box_length": box_length,
            "tolerance_of_unbalanced_force": unbalanced_force_tolerance,
            "tolerance_of_target_mean_stress": stress_tolerance,
            "problem_name": _problem_name(project_parameters),
        }
        with (case_path / "demgen_case_parameters.json").open(
            "w",
            encoding="utf-8",
        ) as parameters_file:
            json.dump(case_parameters, parameters_file, indent=2)

    def _load_particle_radius_distribution(self) -> ParticleRadiusDistribution:
        generation = self.context.parameters.get(
            "random_particle_generation_parameters"
        )
        if not isinstance(generation, Mapping):
            raise ValueError(
                "random_particle_generation_parameters must define the particle "
                "radius distribution."
            )
        random_settings = generation.get("random_variable_settings")
        if not isinstance(random_settings, Mapping):
            raise ValueError(
                "random_particle_generation_parameters.random_variable_settings "
                "must be a JSON object."
            )
        possible_values = random_settings.get("possible_values")
        relative_frequencies = random_settings.get("relative_frequencies")
        if not isinstance(possible_values, list) or not isinstance(
            relative_frequencies,
            list,
        ):
            raise ValueError(
                "random_variable_settings must define possible_values and "
                "relative_frequencies as arrays."
            )
        return ParticleRadiusDistribution(
            tuple(possible_values),
            tuple(relative_frequencies),
        )

    def _load_stability_tolerances(self) -> tuple[float, float]:
        generation = self.context.parameters.get(
            "random_particle_generation_parameters"
        )
        if not isinstance(generation, Mapping):
            raise ValueError(
                "random_particle_generation_parameters must contain the "
                "current DEMGen stability tolerances."
            )
        return (
            _positive_setting(generation, "tolerance_of_unbalanced_force"),
            _positive_setting(
                generation,
                "tolerance_of_target_mean_stress",
            ),
        )


def _positive_setting(settings: Mapping[str, Any], name: str) -> float:
    try:
        value = settings[name]
    except KeyError as error:
        raise ValueError(
            f"random_particle_generation_parameters.{name} is required."
        ) from error
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(
            f"random_particle_generation_parameters.{name} must be greater "
            "than zero."
        )
    return float(value)


def _problem_name(project_parameters: Mapping[str, Any]) -> str:
    problem_name = project_parameters.get("problem_name")
    if not isinstance(problem_name, str) or not problem_name.strip():
        raise ValueError(
            "ProjectParametersDEM.json problem_name must be a non-empty string."
        )
    return problem_name
