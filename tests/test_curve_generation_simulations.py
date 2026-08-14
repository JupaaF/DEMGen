import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = (
    PROJECT_ROOT
    / "example"
    / "test_improved_radius_expansion_with_servo_control_method"
)
RUN_SIMULATIONS = os.environ.get("DEMGEN_RUN_SIMULATION_TESTS") == "1"


@unittest.skipUnless(
    RUN_SIMULATIONS,
    "Set DEMGEN_RUN_SIMULATION_TESTS=1 to run the Kratos simulation suite.",
)
class CurveGenerationSimulationTests(unittest.TestCase):
    def test_single_point_writes_one_complete_checkpoint(self):
        with self.run_simulation(
            {
                "mode": "single_point",
                "target_density": 0.6,
                "target_stress": 100000000.0,
            },
            density_tolerance=0.002,
        ) as case_dir:
            self.assert_successful_case(case_dir)
            self.assertEqual(self.checkpoint_rows(case_dir), 1)
            self.assertTrue((case_dir / "inletPGDEM_target.mdpa").is_file())
            self.assert_density_near_sixty_percent(case_dir)
            self.assert_complete_measurements(case_dir)
            self.assert_gid_checkpoints(case_dir)

    def test_ascending_stress_sweep_saves_every_logarithmic_target(self):
        with self.run_simulation(
            {
                "mode": "stress_sweep",
                "initial_density": 0.6,
                "initial_stress": 100000000.0,
                "final_stress": 400000000.0,
                "number_of_steps": 2,
            },
            density_tolerance=0.002,
        ) as case_dir:
            self.assert_successful_case(case_dir)
            self.assertEqual(
                self.target_sequence(case_dir),
                [100000000.0, 200000000.0, 400000000.0],
            )
            self.assertEqual(self.checkpoint_rows(case_dir), 3)
            for target in (100000000, 200000000, 400000000):
                self.assertTrue((case_dir / f"inletPGDEM_{target}.mdpa").is_file())
            self.assert_density_near_sixty_percent(case_dir)
            self.assert_complete_measurements(case_dir)
            self.assert_gid_checkpoints(case_dir)

    def test_descending_stress_sweep_saves_targets_in_reverse_order(self):
        with self.run_simulation(
            {
                "mode": "stress_sweep",
                "initial_density": 0.6,
                "initial_stress": 400000000.0,
                "final_stress": 100000000.0,
                "number_of_steps": 2,
            },
            density_tolerance=0.002,
        ) as case_dir:
            self.assert_successful_case(case_dir)
            self.assertEqual(
                self.target_sequence(case_dir),
                [400000000.0, 200000000.0, 100000000.0],
            )
            self.assertEqual(self.checkpoint_rows(case_dir), 3)
            self.assert_density_near_sixty_percent(case_dir)
            self.assert_complete_measurements(case_dir)
            self.assert_gid_checkpoints(case_dir)

    def test_density_sweep_saves_only_the_ascending_vertical_curve(self):
        with self.run_simulation(
            {
                "mode": "density_sweep",
                "initial_density": 0.59,
                "final_density": 0.6,
                "initial_stress": 100000000.0,
                "fixed_stress": 400000000.0,
                "number_of_steps": 1,
            },
            density_tolerance=0.002,
            timeout=90,
        ) as case_dir:
            self.assert_successful_case(case_dir)
            self.assertEqual(
                self.target_sequence(case_dir),
                [100000000.0, 400000000.0],
            )
            density_packings = sorted(case_dir.glob("inletPGDEM_density_*.mdpa"))
            self.assertGreaterEqual(len(density_packings), 2)
            self.assertEqual(len(density_packings), self.checkpoint_rows(case_dir))
            self.assertFalse((case_dir / "inletPGDEM_100000000.mdpa").exists())
            self.assertFalse((case_dir / "inletPGDEM_400000000.mdpa").exists())

            densities = self.checkpoint_densities(case_dir)
            self.assertGreater(densities[-1], densities[0])
            self.assertGreaterEqual(densities[-1], 0.598)
            self.assert_density_near_sixty_percent(case_dir)
            self.assert_complete_measurements(case_dir)
            self.assert_gid_checkpoints(case_dir)

    def run_simulation(
        self,
        curve_generation,
        density_tolerance=1.0,
        timeout=120,
    ):
        temporary_case = tempfile.TemporaryDirectory(prefix="demgen-curve-test-")
        run_dir = Path(temporary_case.name)
        self.addCleanup(temporary_case.cleanup)

        parameters = json.loads(
            (EXAMPLE_DIR / "ParametersDEMGen.json").read_text(encoding="utf-8")
        )
        parameters.update(
            {
                "packing_num": 1,
                "domain_length_x": 0.0006,
                "domain_length_y": 0.0006,
                "domain_length_z": 0.0006,
                "particle_radius_max": 0.00005,
                "packing_charcterization_option": False,
                "curve_generation": curve_generation,
            }
        )
        generation = parameters["random_particle_generation_parameters"]
        generation.update(
            {
                "RADIUS": 0.00005,
                "MINIMUM_RADIUS": 0.00005,
                "MAXIMUM_RADIUS": 0.00005,
                "STANDARD_DEVIATION": 0.0,
                "SEED": 7,
                "DO_USE_SEED": True,
                "target_packing_density": 0.6,
                "tolerance_of_packing_density": density_tolerance,
                "tolerance_of_unbalanced_force": 1e12,
                "tolerance_of_target_mean_stress": 1e12,
                "minimum_mean_stress": 1.0,
                "packing_density_delta_list": [0.0],
            }
        )
        generation["random_variable_settings"].update(
            {
                "possible_values": [0.00005],
                "relative_frequencies": [1.0],
                "radius_scale_multiplier": 0.5,
                "do_use_seed": True,
                "seed": 7,
            }
        )
        parameters_path = run_dir / "ParametersDEMGen.json"
        parameters_path.write_text(json.dumps(parameters, indent=2), encoding="utf-8")

        project_parameters = json.loads(
            (EXAMPLE_DIR / "ProjectParametersDEM.json").read_text(encoding="utf-8")
        )
        project_parameters.update(
            {
                "BoundingBoxMaxX": 0.0003,
                "BoundingBoxMaxY": 0.0003,
                "BoundingBoxMaxZ": 0.0003,
                "BoundingBoxMinX": -0.0003,
                "BoundingBoxMinY": -0.0003,
                "BoundingBoxMinZ": -0.0003,
                "MaxTimeStep": 2e-8,
                "FinalTime": 2e-7,
                "GraphExportFreq": 2e-7,
                "VelTrapGraphExportFreq": 2e-7,
                "OutputTimeStep": 2e-7,
            }
        )
        project_parameters["BoundingBoxServoLoadingSettings"].update(
            {
                "BoundingBoxServoLoadingStress": [1.0, 1.0, 1.0],
                "BoundingBoxServoLoadingVelocityMax": 1.0,
                "MeanParticleDiameterD50": 0.0001,
            }
        )
        (run_dir / "ProjectParametersDEM.json").write_text(
            json.dumps(project_parameters, indent=2),
            encoding="utf-8",
        )
        shutil.copyfile(
            EXAMPLE_DIR / "MaterialsDEM.json",
            run_dir / "MaterialsDEM.json",
        )

        environment = os.environ.copy()
        environment["OMP_NUM_THREADS"] = "1"
        process = subprocess.Popen(
            [
                sys.executable,
                PROJECT_ROOT / "src" / "DEMGen_framework_main.py",
                parameters_path,
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                output, _ = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                output, _ = process.communicate()
            self.fail(
                f"DEMGen exceeded the {timeout}-second timeout.\n{output[-12000:]}"
            )

        (run_dir / "simulation.log").write_text(output, encoding="utf-8")
        if process.returncode != 0:
            self.fail(
                f"DEMGen exited with {process.returncode}.\n{output[-12000:]}"
            )

        case_dir = run_dir / "generated_cases" / "case_1"
        return _CaseDirectory(temporary_case, case_dir)

    def assert_successful_case(self, case_dir):
        if not (case_dir / "success.txt").is_file():
            simulation_log = case_dir.parents[1] / "simulation.log"
            generated_files = "\n".join(
                str(path.relative_to(case_dir))
                for path in sorted(case_dir.rglob("*"))
                if path.is_file()
            )
            self.fail(
                "The simulation did not create success.txt.\n"
                f"Generated files:\n{generated_files}\n\n"
                + simulation_log.read_text(encoding="utf-8")[-12000:]
            )
        self.assertTrue((case_dir / "show_packing" / "inletPGDEM.mdpa").is_file())
        gid_files = list((case_dir / "inletPG_Post_Files").glob("*"))
        self.assertTrue(gid_files, "The simulation did not produce GiD results.")
        self.assertGreaterEqual(self.particle_count(case_dir), 200)

    def checkpoint_rows(self, case_dir):
        return len(
            (case_dir / "stress_tensor_save.txt").read_text(encoding="utf-8").splitlines()
        )

    def checkpoint_densities(self, case_dir):
        return [
            float(row.split()[2])
            for row in (case_dir / "stress_tensor_save.txt")
            .read_text(encoding="utf-8")
            .splitlines()
        ]

    def assert_density_near_sixty_percent(self, case_dir):
        for density in self.checkpoint_densities(case_dir):
            self.assertGreaterEqual(density, 0.59)
            self.assertLessEqual(density, 0.61)

    def target_sequence(self, case_dir):
        targets = [
            float(line.split()[1])
            for line in (case_dir / "target_stress.txt")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        sequence = []
        for target in targets:
            if not sequence or target != sequence[-1]:
                sequence.append(target)
        return sequence

    def assert_complete_measurements(self, case_dir):
        rows = (
            (case_dir / "stress_tensor_save.txt")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        self.assertTrue(rows)
        self.assertTrue(all(len(row.split()) == 44 for row in rows))

    def assert_gid_checkpoints(self, case_dir):
        gid_results = list((case_dir / "inletPG_Post_Files").glob("*.post.res"))
        self.assertGreaterEqual(len(gid_results), self.checkpoint_rows(case_dir))

    def particle_count(self, case_dir):
        lines = (case_dir / "inletPGDEM_ini.mdpa").read_text(encoding="utf-8").splitlines()
        begin = lines.index("Begin Nodes") + 1
        end = lines.index("End Nodes")
        return end - begin


class _CaseDirectory:
    def __init__(self, temporary_case, case_dir):
        self.temporary_case = temporary_case
        self.case_dir = case_dir

    def __enter__(self):
        return self.case_dir

    def __exit__(self, exc_type, exc_value, traceback):
        self.temporary_case.cleanup()
