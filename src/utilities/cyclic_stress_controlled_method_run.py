from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import shutil
import sys
import time


project_src = Path(__file__).resolve().parents[1]
if str(project_src) not in sys.path:
    sys.path.insert(0, str(project_src))

import KratosMultiphysics
from KratosMultiphysics import DELTA_TIME, RADIUS, TIME
from KratosMultiphysics.DEMApplication.DEM_analysis_stage import DEMAnalysisStage
from KratosMultiphysics.restart_utility import RestartUtility

from cyclic_stress_control import (
    CHECKPOINT_STATE_FILENAME,
    CYCLIC_SERVO_VELOCITY_MAX,
    CYCLIC_SETTLING_SERVO_VELOCITY_MAX,
    HIGH_PRESSURE_PHASE,
    LOW_PRESSURE_PHASE,
    PROGRESS_REPORT_FREQUENCY_STEPS,
    STRESS_MEASUREMENT_FREQUENCY_STEPS,
    TARGET_STRESS_PHASE,
    CyclicStressControlledSettings,
    CyclicStressController,
    cycle_pressure_threshold_crossed,
    enclosing_measurement_sphere,
    immediate_cycle_pressure_target,
    phase_stress_tolerance,
)
from demgen_case_parameters import load_case_parameters
from particles import ParticlePacking, SphericalParticle


MODEL_PART_NAMES = (
    "SpheresPart",
    "RigidFacePart",
    "ClusterPart",
    "DEMInletPart",
    "MappingPart",
    "ContactPart",
)
BOX_BOUND_NAMES = (
    "BoundingBoxMinX",
    "BoundingBoxMinY",
    "BoundingBoxMinZ",
    "BoundingBoxMaxX",
    "BoundingBoxMaxY",
    "BoundingBoxMaxZ",
)


class CyclicStressControlledAnalysis(DEMAnalysisStage):
    def __init__(
        self,
        model,
        project_parameters,
        case_parameters,
        checkpoint=None,
    ):
        super().__init__(model, project_parameters)
        self.parameters = project_parameters
        self.case_parameters = case_parameters
        settings = CyclicStressControlledSettings(
            **case_parameters["cyclic_stress_controlled"]
        )
        self.controller = (
            CyclicStressController.from_state(settings, checkpoint["controller"])
            if checkpoint is not None
            else CyclicStressController(settings)
        )
        self.checkpoint = checkpoint
        self.maximum_particle_radius = float(
            case_parameters.get(
                "maximum_particle_radius",
                case_parameters.get("particle_radius", 0.0),
            )
        )
        if self.maximum_particle_radius <= 0.0:
            raise ValueError(
                "Case parameters must define a positive maximum particle radius."
            )
        self.completed = False
        self.last_flush = time.time()

    def Initialize(self):
        super().Initialize()
        self.steps_since_measurement = 0
        self.steps_since_report = 0
        self.measured_stresses: deque[float] = deque(maxlen=6)
        self.tolerance_of_unbalanced_force = self.case_parameters[
            "tolerance_of_unbalanced_force"
        ]
        self.tolerance_of_target_mean_stress = self.case_parameters[
            "tolerance_of_target_mean_stress"
        ]
        self.parameters["BoundingBoxMoveOption"].SetBool(True)
        self.parameters["BoundingBoxServoLoadingOption"].SetBool(True)
        self.waiting_for_threshold_stability = False
        self.restart_utilities = self._create_restart_utilities()
        self._set_target_pressure(
            self.controller.target_pressure,
            self._measure_mean_stress(),
        )
        self._report(
            ("resuming" if self.checkpoint is not None else "starting")
            + " with "
            f"target_density={self.controller.settings.target_packing_density:.6f}, "
            f"minimum_pressure={self.controller.minimum_cycle_pressure:.6f} Pa, "
            f"target_stress={self.controller.settings.target_stress:.6f} Pa, "
            f"completed_cycles={self.controller.completed_cycles}"
        )

    def ReadModelPartsFromRestartFile(self, model_part_import_settings):
        settings = json.loads(model_part_import_settings.PrettyPrintJsonString())
        input_names = settings.pop("input_filenames")
        settings.pop("input_type", None)
        for model_part_name in input_names:
            part_settings = dict(settings)
            part_settings["input_filename"] = model_part_name
            RestartUtility(
                self.model.GetModelPart(model_part_name),
                KratosMultiphysics.Parameters(json.dumps(part_settings)),
            ).LoadRestart()

    def KeepAdvancingSolutionLoop(self):
        return not self.completed and self.time < self.end_time

    def OutputSolutionStep(self):
        super().OutputSolutionStep()
        self.steps_since_measurement += 1
        self.steps_since_report += 1
        if self.steps_since_measurement < STRESS_MEASUREMENT_FREQUENCY_STEPS:
            return
        self.steps_since_measurement = 0

        mean_stress = self._measure_mean_stress()
        current_phase = self.controller.phase
        if (
            current_phase in {HIGH_PRESSURE_PHASE, LOW_PRESSURE_PHASE}
            and not self.waiting_for_threshold_stability
        ):
            if cycle_pressure_threshold_crossed(
                current_phase,
                mean_stress,
                self.controller.target_pressure,
            ):
                self._slow_box_for_threshold_stability(mean_stress)
            else:
                self._update_immediate_cycle_target(mean_stress)

        self.measured_stresses.append(mean_stress)
        if self.waiting_for_threshold_stability:
            stress_is_stable = self._stress_is_stable()
        elif current_phase == TARGET_STRESS_PHASE:
            stress_is_stable = self._stress_is_stable()
        else:
            stress_is_stable = False
        unbalanced_force = (
            self._measure_unbalanced_force() if stress_is_stable else None
        )
        is_stable = (
            stress_is_stable
            and unbalanced_force is not None
            and unbalanced_force < self.tolerance_of_unbalanced_force
        )
        should_report = (
            self.steps_since_report >= PROGRESS_REPORT_FREQUENCY_STEPS
        )
        packing_density = None
        if should_report or is_stable:
            packing_density = self._measure_packing_density()
            self._report_periodically(
                packing_density,
                mean_stress,
                unbalanced_force,
            )
            self.steps_since_report = 0
        if not is_stable:
            return
        assert packing_density is not None

        if self.waiting_for_threshold_stability:
            transition_reason = "stable after cycle threshold crossing"
            next_pressure = self.controller.register_stable_cycle_threshold(
                packing_density
            )
            self.waiting_for_threshold_stability = False
        else:
            assert current_phase == TARGET_STRESS_PHASE
            transition_reason = "stable final target reached"
            next_pressure = self.controller.register_stable_state(
                packing_density
            )

        self._report(
            f"{transition_reason}: phase={current_phase}, "
            f"cycle={self.controller.completed_cycles}, "
            f"stress={mean_stress:.6f} Pa, density={packing_density:.6f}"
        )
        if self.controller.succeeded:
            self._write_successful_packing()
            self._discard_checkpoint()
            self.completed = True
            return
        if self.controller.failed:
            raise RuntimeError(self.controller.failure_message)

        if current_phase == TARGET_STRESS_PHASE:
            self._report(
                f"cycle={self.controller.completed_cycles} did not reach the "
                "requested density; next minimum pressure="
                f"{self.controller.minimum_cycle_pressure:.6f} Pa"
            )
        self._set_target_pressure(next_pressure, mean_stress)
        self._save_checkpoint()

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        now = time.time()
        if now - self.last_flush > 10.0:
            sys.stdout.flush()
            self.last_flush = now

    def _set_target_pressure(
        self,
        target_pressure: float,
        measured_stress: float,
    ) -> None:
        self.parameters["BoundingBoxMoveOption"].SetBool(True)
        self._set_servo_velocity_max(CYCLIC_SERVO_VELOCITY_MAX)
        if self.controller.phase in {HIGH_PRESSURE_PHASE, LOW_PRESSURE_PHASE}:
            immediate_target = immediate_cycle_pressure_target(
                self.controller.phase,
                measured_stress,
                self.controller.minimum_cycle_pressure,
                self.controller.settings.maximum_cycle_pressure,
            )
        else:
            immediate_target = target_pressure
        self._set_servo_pressure(immediate_target)
        self.measured_stresses.clear()
        self._report(
            f"seeking phase={self.controller.phase}, "
            f"phase_limit={target_pressure:.6f} Pa, "
            f"immediate_target={immediate_target:.6f} Pa"
        )

    def _update_immediate_cycle_target(self, mean_stress: float) -> None:
        immediate_target = immediate_cycle_pressure_target(
            self.controller.phase,
            mean_stress,
            self.controller.minimum_cycle_pressure,
            self.controller.settings.maximum_cycle_pressure,
        )
        self._set_servo_pressure(immediate_target)

    def _set_servo_pressure(self, target_pressure: float) -> None:
        self.immediate_target_pressure = target_pressure
        self.parameters["BoundingBoxServoLoadingSettings"][
            "BoundingBoxServoLoadingStress"
        ].SetVector([target_pressure, target_pressure, target_pressure])

    def _slow_box_for_threshold_stability(self, mean_stress: float) -> None:
        self._set_servo_pressure(self.controller.target_pressure)
        self._set_servo_velocity_max(CYCLIC_SETTLING_SERVO_VELOCITY_MAX)
        self.waiting_for_threshold_stability = True
        self.measured_stresses.clear()
        self._report(
            f"threshold crossed in phase={self.controller.phase} at "
            f"stress={mean_stress:.6f} Pa; limiting box servo to "
            f"{CYCLIC_SETTLING_SERVO_VELOCITY_MAX:.6f} m/s until stable"
        )

    def _set_servo_velocity_max(self, maximum_velocity: float) -> None:
        self.parameters["BoundingBoxServoLoadingSettings"][
            "BoundingBoxServoLoadingVelocityMax"
        ].SetDouble(maximum_velocity)

    def _measure_packing_density(self) -> float:
        volume = (
            (self.BoundingBoxMaxX_update - self.BoundingBoxMinX_update)
            * (self.BoundingBoxMaxY_update - self.BoundingBoxMinY_update)
            * (self.BoundingBoxMaxZ_update - self.BoundingBoxMinZ_update)
        )
        if volume <= 0.0:
            raise RuntimeError("The servo-controlled box has non-positive volume.")
        return self.MeasureTotalSpheresVolume() / volume

    def _measure_mean_stress(self) -> float:
        stress_tensor = self.MeasureSphereForGettingGlobalStressTensor()
        return sum(stress_tensor[index][index] for index in range(3)) / 3.0

    def _measure_unbalanced_force(self) -> float:
        center, measurement_radius = enclosing_measurement_sphere(
            (
                self.BoundingBoxMinX_update,
                self.BoundingBoxMinY_update,
                self.BoundingBoxMinZ_update,
            ),
            (
                self.BoundingBoxMaxX_update,
                self.BoundingBoxMaxY_update,
                self.BoundingBoxMaxZ_update,
            ),
            self.maximum_particle_radius,
        )
        return self.MeasureSphereForGettingPackingProperties(
            measurement_radius,
            center[0],
            center[1],
            center[2],
            "unbalanced_force",
        )

    def _stress_is_stable(self) -> bool:
        if len(self.measured_stresses) < self.measured_stresses.maxlen:
            return False
        mean_absolute_stress_error = sum(
            abs(stress - self.controller.target_pressure)
            for stress in tuple(self.measured_stresses)[-5:]
        ) / 5.0
        stress_tolerance = phase_stress_tolerance(
            self.controller.target_pressure,
            self.tolerance_of_target_mean_stress,
        )
        return mean_absolute_stress_error < stress_tolerance

    def _create_restart_utilities(self):
        utilities = []
        for model_part_name in MODEL_PART_NAMES:
            settings = KratosMultiphysics.Parameters(
                json.dumps(
                    {
                        "input_filename": model_part_name,
                        "serializer_trace": "no_trace",
                        "restart_save_frequency": 0.0,
                        "restart_control_type": "time",
                        "save_restart_files_in_folder": True,
                        "max_files_to_keep": 2,
                    }
                )
            )
            utility = RestartUtility(
                self.model.GetModelPart(model_part_name),
                settings,
            )
            utility.CreateOutputFolder()
            utilities.append(utility)
        return utilities

    def _save_checkpoint(self) -> None:
        for utility in self.restart_utilities:
            utility.model_part.ProcessInfo[TIME] = self.time
            utility.SaveRestart()
        label = str(float(f"{self.time:.12g}"))
        restart_files = [
            f"{name}__restart_files/{name}_{label}.rest"
            for name in MODEL_PART_NAMES
        ]
        checkpoint = {
            "version": 1,
            "settings": self.controller.settings.to_dict(),
            "controller": self.controller.to_state(),
            "time": self.time,
            "restart_label": label,
            "restart_files": restart_files,
            "box_bounds": {
                "BoundingBoxMinX": self.BoundingBoxMinX_update,
                "BoundingBoxMinY": self.BoundingBoxMinY_update,
                "BoundingBoxMinZ": self.BoundingBoxMinZ_update,
                "BoundingBoxMaxX": self.BoundingBoxMaxX_update,
                "BoundingBoxMaxY": self.BoundingBoxMaxY_update,
                "BoundingBoxMaxZ": self.BoundingBoxMaxZ_update,
            },
        }
        state_path = Path(CHECKPOINT_STATE_FILENAME)
        temporary_path = state_path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(checkpoint, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(state_path)
        if self.checkpoint is not None:
            self._remove_restart_files(self.checkpoint.get("restart_files", []))
        self.checkpoint = checkpoint
        self._report(
            f"checkpoint saved after phase transition at time={self.time:.12g} s"
        )

    def _discard_checkpoint(self) -> None:
        if self.checkpoint is not None:
            self._remove_restart_files(self.checkpoint.get("restart_files", []))
        state_path = Path(CHECKPOINT_STATE_FILENAME)
        if state_path.is_file() and not state_path.is_symlink():
            state_path.unlink()
        self.checkpoint = None

    @staticmethod
    def _remove_restart_files(relative_paths) -> None:
        working_directory = Path.cwd().resolve()
        for relative_path in relative_paths:
            candidate = Path(relative_path)
            if candidate.is_absolute() or ".." in candidate.parts:
                continue
            resolved = (working_directory / candidate).resolve()
            if working_directory not in resolved.parents:
                continue
            if resolved.is_file() and not resolved.is_symlink():
                resolved.unlink()

    def _write_successful_packing(self) -> None:
        element_ids_by_node = {
            element.GetNode(0).Id: element.Id
            for element in self.spheres_model_part.Elements
        }
        particles = ParticlePacking(
            SphericalParticle(
                node_id=node.Id,
                element_id=element_ids_by_node[node.Id],
                position=(node.X, node.Y, node.Z),
                radius=node.GetSolutionStepValue(RADIUS),
            )
            for node in self.spheres_model_part.Nodes
        )
        output_name = f"{self.case_parameters['problem_name']}DEM.mdpa"
        particles.write_mdpa(output_name)

        show_path = Path("show_packing")
        if show_path.exists():
            shutil.rmtree(show_path)
        show_path.mkdir()
        particles.write_mdpa(show_path / output_name)
        shutil.copyfile("MaterialsDEM.json", show_path / "MaterialsDEM.json")
        shutil.copyfile("show_packing.py", show_path / "show_packing.py")
        self._write_show_project_parameters(show_path)

        Path("success.txt").write_text(
            "Simulation completed successfully.",
            encoding="utf-8",
        )
        self._report(
            f"completed after {self.controller.completed_cycles} cycles at "
            f"minimum_pressure={self.controller.minimum_cycle_pressure:.6f} Pa"
        )

    def _write_show_project_parameters(self, show_path: Path) -> None:
        with Path("ProjectParametersDEM.json").open(encoding="utf-8") as source:
            project_parameters = json.load(source)
        project_parameters.update(
            {
                "BoundingBoxMaxX": self.BoundingBoxMaxX_update,
                "BoundingBoxMaxY": self.BoundingBoxMaxY_update,
                "BoundingBoxMaxZ": self.BoundingBoxMaxZ_update,
                "BoundingBoxMinX": self.BoundingBoxMinX_update,
                "BoundingBoxMinY": self.BoundingBoxMinY_update,
                "BoundingBoxMinZ": self.BoundingBoxMinZ_update,
                "BoundingBoxMoveOption": False,
                "BoundingBoxServoLoadingOption": False,
                "FinalTime": 2.0 * self.spheres_model_part.ProcessInfo[DELTA_TIME],
            }
        )
        with (show_path / "ProjectParametersDEM.json").open(
            "w",
            encoding="utf-8",
        ) as destination:
            json.dump(project_parameters, destination, indent=2)

    def _report_periodically(
        self,
        packing_density: float,
        mean_stress: float,
        unbalanced_force: float | None,
    ) -> None:
        unbalanced_text = (
            f"{unbalanced_force:.6g}"
            if unbalanced_force is not None
            else "not_checked"
        )
        self._report(
            f"phase={self.controller.phase}, "
            f"cycle={self.controller.completed_cycles}, "
            f"stress={mean_stress:.6f} Pa, "
            f"immediate_target={self.immediate_target_pressure:.6f} Pa, "
            f"phase_limit={self.controller.target_pressure:.6f} Pa, "
            f"density={packing_density:.6f}/"
            f"{self.controller.settings.target_packing_density:.6f}, "
            f"unbalanced_force={unbalanced_text}"
        )

    @staticmethod
    def _report(message: str) -> None:
        print(f"[cyclic_stress_controlled] {message}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-parameters", required=True)
    arguments = parser.parse_args()
    case_parameters = load_case_parameters(arguments.case_parameters)

    checkpoint = _load_checkpoint(case_parameters)
    with Path("ProjectParametersDEM.json").open(encoding="utf-8") as parameter_file:
        project_parameters = json.load(parameter_file)
    if checkpoint is not None:
        project_parameters.update(checkpoint["box_bounds"])
        project_parameters.setdefault("solver_settings", {})[
            "model_import_settings"
        ] = {
            "input_type": "rest",
            "serializer_trace": "no_trace",
            "input_filenames": list(MODEL_PART_NAMES),
            "restart_load_file_label": checkpoint["restart_label"],
            "load_restart_files_from_folder": True,
        }
    parameters = KratosMultiphysics.Parameters(json.dumps(project_parameters))
    analysis = CyclicStressControlledAnalysis(
        KratosMultiphysics.Model(),
        parameters,
        case_parameters,
        checkpoint,
    )
    analysis.Run()
    if not analysis.completed:
        raise RuntimeError(
            "The cyclic stress-controlled system reached FinalTime before a "
            "stable packing with the requested density and stress was found."
        )


def _load_checkpoint(case_parameters):
    state_path = Path(CHECKPOINT_STATE_FILENAME)
    if not state_path.is_file():
        return None
    checkpoint = json.loads(state_path.read_text(encoding="utf-8"))
    settings = CyclicStressControlledSettings(
        **case_parameters["cyclic_stress_controlled"]
    )
    if checkpoint.get("version") != 1:
        raise RuntimeError("Unsupported cyclic stress checkpoint version.")
    if checkpoint.get("settings") != settings.to_dict():
        raise RuntimeError(
            "Checkpoint settings differ from the current cyclic stress settings."
        )
    restart_files = checkpoint.get("restart_files")
    restart_label = checkpoint.get("restart_label")
    if not isinstance(restart_label, str) or not restart_label:
        raise RuntimeError("Checkpoint contains an invalid restart label.")
    expected_restart_files = [
        f"{name}__restart_files/{name}_{restart_label}.rest"
        for name in MODEL_PART_NAMES
    ]
    if not isinstance(restart_files, list) or len(restart_files) != len(
        MODEL_PART_NAMES
    ):
        raise RuntimeError("Checkpoint does not list every DEM restart file.")
    if restart_files != expected_restart_files:
        raise RuntimeError("Checkpoint restart file names are inconsistent.")
    bounds = checkpoint.get("box_bounds")
    if not isinstance(bounds, dict) or set(bounds) != set(BOX_BOUND_NAMES):
        raise RuntimeError("Checkpoint contains invalid bounding-box limits.")
    if not all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in bounds.values()
    ):
        raise RuntimeError("Checkpoint bounding-box limits must be numeric.")
    missing_files = [
        path
        for path in restart_files
        if not Path(path).is_file()
    ]
    if missing_files:
        raise RuntimeError(
            "Checkpoint is incomplete; missing restart files: "
            + ", ".join(missing_files)
        )
    return checkpoint


if __name__ == "__main__":
    main()
